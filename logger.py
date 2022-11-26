from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from collections import deque

from threading import Thread
from elasticsearch.helpers import parallel_bulk, bulk

import tqdm
import os
import sys
import time

from elastic import es
from parser import Parser

class serverUpdater:
    def __init__(self, app, socketio):
        self.servers = os.listdir("logs")

        self.app = app
        self.socketio = socketio

        self.runnings = {}

        for server in self.servers:
        
            logs = os.listdir(f"logs/{server}")
            init_len = len(logs)

            for i in range(init_len):
                    log = logs.pop(0)

                    if i == init_len - 1:
                        self.runnings[server] = fileParser(server, log, self, True)
                        self.runnings[server].start()
                    else:
                        fileParser(server, log, self).start()


        self.handler = newLogHandler(self)
        self.observer = Observer()

        self.observer.schedule(self.handler, path='logs\\', recursive=True)
        self.observer.start()

class newLogHandler(FileSystemEventHandler):
    def __init__(self, updater) -> None:
        self.updater = updater

    def on_any_event(self, event):
        print(event.event_type, event.src_path)

    def on_created(self, event):
        server = event.src_path.split("\\")[-2]
        file = event.src_path.split("\\")[-1]

        print("E", server, file)

        self.updater.runnings[server].running = False
        self.updater.runnings[server] = fileParser(server, file, self.updater, True, new=True)
        self.updater.runnings[server].start()

        print("on_created", event.src_path.split("\\")[-1])


def generate_actions(path, server, current_parser=None, initial=False):
    def send_in_thread(parsed):
        _parsed = parsed
        _parsed["time"] = datetime.strftime(parsed["time"], "%Y-%m-%dT%H:%M:%S")
        result = {
            "status": 1,
            "append": True,
            "count": 1,
            "items": [_parsed]
        }

        current_parser.updater.socketio.emit("API:NEW_LOG", result, to="LOGS_STREAM")
        current_parser.updater.socketio.emit("API:NEW_LOG", result, to=f"LOGS_STREAM_{server}")
        
        if parsed["warn"]:
            current_parser.updater.socketio.emit("API:GET_WARNS", result, to="LOGS_STREAM")
            current_parser.updater.socketio.emit("API:GET_WARNS", result, to=f"LOGS_STREAM_{server}")

    with open(path, mode="r") as f:
        batch = []
        chunk = 0
        total = 0

        ended = False
        while current_parser.running:
            try:
                if chunk == 1000:
                    deque(parallel_bulk(es, batch, thread_count=10), maxlen=0)

                    chunk = 0
                    del batch[:]
                    print(total)


                line = f.readline()
                if line:

                    parsed = Parser.parse(line, server)
                    if ended or current_parser.new:
                        Thread(target=send_in_thread, args=(parsed, )).start()

                    if ended:
                        print(parsed["time"])
                    batch.append({"_index": "logs",
                                    "_source": parsed
                                        })

                    chunk += 1
                    total += 1
                    continue

                if not(current_parser.last):
                    break

                if chunk:
                    print(batch[0])
                    deque(parallel_bulk(es, batch, thread_count=10), maxlen=0)

                    print(chunk)
                    chunk = 0
                    del batch[:]

                ended = True
            
            except Exception as e:
                try:
                    batch[0]["_source"]["time"] = datetime.strptime(parsed["time"], "%Y-%d-%mT%H:%M:%S")
                except:
                    print(e, batch)

                print(e, batch)
                time.sleep(0.1)

class fileParser(Thread):
    def __init__(self, server, file, updater, last=False, new=False) -> None:
        Thread.__init__(self)
        
        self.updater = updater

        self.server = server
        self.file = file
        self.last = last
        self.new = new

        self.running = True
        self.bulk_running = True

    def run(self):
        global es
        
        progress = tqdm.tqdm(unit=self.file, total=400000)
        successes = 0
        
        generate_actions(path=f"logs/{self.server}/{self.file}", server=self.server, current_parser=self, initial=True)
        
        print("done")