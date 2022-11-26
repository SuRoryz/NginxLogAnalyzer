from flask import Flask, render_template, request, flash, g
from flask_sqlalchemy import SQLAlchemy
import time
import linecache
from parser import Parser
import os
import sys

from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Thread

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:15122003@localhost/logBase'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)

class currentFile(db.Model):
    server = db.Column(db.String(50))
    filename = db.Column(db.String(50), primary_key=True)
    last_line = db.Column(db.Integer, default=0)

    def __init__(self, server, filename):
        self.server = server
        self.filename = filename

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String())
    remote_addr = db.Column(db.String())
    time = db.Column(db.DateTime(timezone=True))
    request_method = db.Column(db.String())
    request_url = db.Column(db.String())
    resuest_protocol = db.Column(db.String())
    request_status = db.Column(db.String())
    request_size = db.Column(db.String())
    http_reffer = db.Column(db.String())
    user_agent = db.Column(db.String())

    def __init__(self, remote_addr, remote_user, time, request_method, request_url, resuest_protocol, request_status, request_size, http_reffer, user_agent, server):
        self.remote_addr = remote_addr
        self.remote_user = remote_user
        self.time = time
        self.request_method = request_method
        self.request_url = request_url
        self.resuest_protocol = resuest_protocol
        self.request_status = request_status
        self.request_size = request_size
        self.http_reffer = http_reffer
        self.user_agent = user_agent
        self.server = server
    
class serverUpdater(Thread):
    def __init__(self, server):
        Thread.__init__(self)

        self.server = server

        self.fileList = os.listdir(f"logs/{self.server}")
        self.init_len = len(self.fileList)

        self.fileObj = currentFile.query.filter_by(server=self.server).first()

        self.currentRunningParser = None

        self.fileEnd = True

        self.session = db.session

        if not(self.fileObj):
            self.fileObj = currentFile(self.server, self.fileList.pop(0))

        self.currentFile = self.fileObj.filename
        self.currentFileLine = self.fileObj.last_line

    def run(self):
        while True:
            if self.fileEnd:
                try:
                    self.currentFile = self.fileList.pop(0)
                except Exception as e:
                    print("E", e)
                    if len(os.listdir(f"logs/{self.server}")) > self.init_len:
                        self.fileList = os.listdir(f"logs/{self.server}")
                        self.init_len = len(self.fileList)

                        continue

                    self.currentFileLine = 0

                    print("ASSSSSSSSS", self.currentFile)
                    self.fileObj = currentFile(self.server, self.currentFile)
                    print(self.fileObj)

                    self.fileObj.filename = self.currentFile
                    self.fileObj.last_line = self.currentFileLine

                    self.currentRunningParser = fileParser(self, last=True)
                    self.currentRunningParser.start()

                    self.fileEnd = False

                    db.session.add(self.fileObj)

                    continue

                self.currentFileLine = 0

                self.fileObj.filename = self.currentFile
                self.fileObj.last_line = self.currentFileLine

                self.session(self.fileObj)

                fileParser(self).start()

                self.fileEnd = False

            time.sleep(0.1)
    
    def addLineCount(self, count=1):
        self.currentFileLine += count


class fileParser(Thread):
    def __init__(self, updater, last=True):
        Thread.__init__(self)

        self.updater = updater
        self.last = last
        self.session = db.session

        self.sycner = dbSyncerLog(self)
        self.sycner.start()
    
    def run(self):
        file = self.updater.currentFile
        
        while True:
            try:
                last_line = self.updater.currentFileLine

                try:
                    #print(last_line + 1, self.updater.server)
                    line = linecache.getline(f"logs/{self.updater.server}/{file}", last_line + 1)
                except Exception as e:
                    print(e)
                    if not(self.last):
                        self.updater.fileEnd = True
                        sys.exit(0)
                    continue

                parsed_file = Parser.parse(line, self.updater.server)

                db.session.add(Log(*[parsed_file[key] for key in parsed_file]))
                db.session.commit()
                self.updater.addLineCount()
                #print(self.updater.currentFileLine)
            except Exception as e:
                self.updater.addLineCount()
                print(line, e)

            #time.sleep(1)

class dbSyncer(Thread):
    def __init__(self, updater):
        Thread.__init__(self)
        self.updater = updater

    def run(self):
        while True:
            try:
                self.updater.fileObj.last_line = self.updater.currentFileLine
                print("commit")

                self.updater.session.commit()
            except Exception as e:
                print(e)
                pass
                
            time.sleep(1)
    
class dbSyncerLog(Thread):
    def __init__(self, parser):
        Thread.__init__(self)
        self.parser = parser

    def run(self):
        while True:
            try:
                self.parser.session.commit()
            except Exception as e:
                print(e)
                pass
                
            time.sleep(1)

if __name__ == "__main__":
    db.create_all()

    if not(currentFile.query.first()):
        db.session.commit()
    
    for server in os.listdir("logs/"):
        updater = serverUpdater(server)
        updater.start()
        dbSyncer(updater).start()

    app.run()


