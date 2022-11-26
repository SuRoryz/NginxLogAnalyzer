from datetime import datetime
from flask import Flask, render_template, request, flash, g
from flask_sqlalchemy import SQLAlchemy

from elastic import es, create_index
from logger import serverUpdater

from flask_socketio import SocketIO, emit, join_room, leave_room
from threading import Thread

from json import loads, dumps
import time
import os

app = Flask(__name__)
socketio = SocketIO(app)

available_servers = os.listdir("logs")

@socketio.on('API:HOOK_LOGS')
def API_HOOK_LOGS(data):
    server = "ALL"

    data = loads(data)

    if "server" in data:
        server = data["server"]
    
    leave_room("LOGS_STREAM")
    for server in available_servers:
        leave_room(f"LOGS_STREAM_{server}")

    if server == "ALL":
        join_room("LOGS_STREAM")
    else:
        join_room(f"LOGS_STREAM_{server}")


    emit("API:HOOKED", {"status": 1})

@socketio.on('API:GET_TOTALS')
def API_GET_TOTALS(data):
    server = "ALL"

    data = loads(data)

    if "server" in data:
        server = data["server"]
    
    body = {'size': 0,"track_total_hits": True, 'aggs':{"today": {"date_range": {"field": "time", "ranges": {"from": "now-1d", "to": "now"}}, "aggs": {
                                                                        "warns_today": {"filter": {"match": {"warn": {"query": True}}}},
                                                                        "flow_today": {"sum": {"field": "request_size"}}
                                                                    }},
                                                        "warns_total": {"filter": {"match": {"warn": {"query": True}}}},
                                                        "flow_total": {"sum": {"field": "request_size"}}}}

    if server != "ALL":
        body["query"] = {"bool": {"must": {"match": {"server": server}}}}

    resp = es.search(index="logs", body=body)


    result = {
        "status": 1,
        "count": len(resp['hits']['hits']),
        "items": {
            "hits": {
                "today": resp["aggregations"]["today"]["buckets"][0]["doc_count"],
                "total": resp['hits']['total']["value"],
            },
            "warns": {
                "today": resp["aggregations"]["today"]["buckets"][0]["warns_today"]['doc_count'],
                "total": resp["aggregations"]["warns_total"]["doc_count"],
            },
            "flow": {
                "today": int(resp["aggregations"]["today"]["buckets"][0]["flow_today"]['value']),
                "total": int(resp["aggregations"]["flow_total"]["value"]),
            },
        }
    }

    emit("API:GET_TOTALS", result)

@socketio.on('API:GET_TOP_URLS')
def API_GET_TOP_URLS(data):
    count = 10
    with_user = True
    server = "ALL"
    minutes_since = 10

    data = loads(data)

    if "count" in data:
        count = data["count"]
    if "with_user" in data:
        with_user = data["with_user"]
    if "server" in data:
        server = data["server"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]

    query = {"bool": {"must": [{"range": {"time": {"from": f"now-{minutes_since}m", "to": "now"}}}]}}

    body = {"query": query, "aggs": {"urls": {"terms": {"field": "request_url", "order": { "_count": "desc" }}}}}

    if with_user:
        body["aggs"]["urls"]["aggs"] = {"top_user": {"terms": {"field": "remote_addr", "size": 1, "order": {"_count": "desc"}}}}
    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server": server}})

    resp = es.search(index="logs", body=body)

    result = {
        "status": 1,
        "count": len(resp['hits']['hits']),
        "items": resp['aggregations']['urls']['buckets'][:count]
    }

    emit("API:GET_TOP_URLS", result)

@socketio.on('API:GET_TOP_GROUP')
def API_GET_TOP_ERRORS(data):
    count = 10
    with_user = True
    server = "ALL"
    param = "request_status"
    minutes_since = 10

    data = loads(data)

    if "count" in data:
        count = data["count"]
    if "with_user" in data:
        with_user = data["with_user"]
    if "server" in data:
        server = data["server"]
    if "param" in data:
        param = data["param"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]

    query = {"bool": {"must": [{"range": {"time": {"from": f"now-{minutes_since}m", "to": "now"}}}]}}

    body = {"query": query, "aggs": {"group": {"terms": {"field": param, "order": { "_count": "desc" }}}}}
    if with_user:
        body["aggs"]["group"]["aggs"] = {"top_user": {"terms": {"field": "remote_addr", "size": 1, "order": {"_count": "desc"}}}}
    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server": server}})

    resp = es.search(index="logs", body=body)
    
    result = {
        "status": 1,
        "count": len(resp['hits']['hits']),
        "items": resp['aggregations']['group']['buckets'][:count]
    }

    emit("API:GET_TOP_GROUP", result)

@socketio.on('API:GET_TOP_IPS')
def API_GET_TOP_IPS(data):
    count = 10
    by_warns = None
    server = "ALL"
    minutes_since = 10

    data = loads(data)

    if "count" in data:
        count = data["count"]
    if "by_warns" in data:
        by_warns = data["by_warns"]
    if "server" in data:
        server = data["server"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]

    query = {"bool": {"must": [{"range": {"time": {"from": f"now-{minutes_since}m", "to": "now"}}}]}}

    body = {"query": query, "aggs": {"ips": {"terms": {"field": "remote_addr", "order": { "_count": "desc" }}, "aggs": {"warns": {"terms": {"field": "warn"}}}}}}

    if by_warns:
        body["query"]["bool"]["must"].append({"match": {"warn": True}})
    
    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server": server}})

    
    resp = es.search(index="logs", body=body)

    result = {
        "status": 1,
        "count": len(resp['hits']['hits']),
        "by_warns": by_warns,
        "items": resp['aggregations']['ips']['buckets'][:count]
    }

    emit("API:GET_TOP_IPS", result)

    

@socketio.on('API:GET_LOGS')
def API_GET_LOGS(data):
    count = 10
    server = "ALL"
    order = None
    minutes_since = 10

    data = loads(data)

    if "count" in data:
        count = data["count"]
    if "server" in data:
        server = data["server"]
    if "order" in data:
        order = data["order"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]
    
    query = {"bool": {"must": [{"range": {"time": {"to": f"from-{minutes_since}m", "to": "now"}}}]}}

    if server != "ALL":
        query["bool"]["must"].append({"match": {"server": server}})

    resp = es.search(index="logs", sort= [{"time": {"order": "desc"}}], query=query, size=count)

    result = {
        "status": 1,
        "count": len(resp['hits']['hits']),
        "new": True,
        "items": [record["_source"] for record in resp['hits']['hits']]
    }

    emit("API:NEW_LOG", result)

@socketio.on("API:GET_PER")
def API_GET_PER(data):
    interval = "1m"
    minutes_since = 10
    server = "ALL"

    data = loads(data)

    if "interval" in data:
        interval = data["interval"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]
    if "server" in data:
        server = data["server"]

    if minutes_since >= 42000:
        interval = "1h"

        if minutes_since >= 1200000:
            interval = "1d"
    body = {"query": {"bool": {"must": [{"range": {"time": {"from": f"now-{minutes_since}m", "to": "now"} }}] } }, "aggs": {f"hits": {"date_histogram": {"extended_bounds": {"max": "now"}, "field": "time", "fixed_interval": interval, "min_doc_count": 0}}}}
    
    if interval != "1d":
        body["aggs"]["hits"]["date_histogram"]["extended_bounds"]["min"] = f"now-{minutes_since}m"
    
    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server": server}})
    
    resp = es.search(index="logs", body=body)

    emit("API:GET_PER", {'status': 1, 'items': resp['aggregations']['hits']['buckets'][-minutes_since:]})

@socketio.on("API:GET_WARNS")
def API_GET_WARNS(data):
    count = 10
    server = "ALL"
    minutes_since = 10

    data = loads(data)

    if "count" in data:
        count = data["count"]
    if "server" in data:
        server = data["server"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]

    body = {"sort": [{"time": {"order": "desc"}}], "query": {"bool": {"must": [{"range": {"time": {"from": f"now-{minutes_since}m", "to": "now"}}}, {"match": {"warn": True}}]}}, "size": count}

    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server":  server}})

    resp = es.search(index="logs", body=body)

    emit("API:GET_WARNS", {'status': 1, 'items': resp["hits"]["hits"]})


@socketio.on("API:GET_WARNS_COUNT")
def API_GET_WARNS_COUNT(data):
    interval = "1m"
    minutes_since = 10
    server = "ALL"

    data = loads(data)

    if "interval" in data:
        interval = data["interval"]
    if "minutes_since" in data:
        minutes_since = data["minutes_since"]
    if "server" in data:
        server = data["server"]

    if minutes_since >= 42000:
        interval = "1h"

        if minutes_since >= 1200000:
            interval = "1d"

    body = {"query": {"bool": {"must": [{"range": {"time": {"to": "now", "from": f"now-{minutes_since}m" } } }]}}, "aggs": {"warns": {"terms": {"field": "warn"}, "aggs": {"warns_true": {"date_histogram": {"extended_bounds": {"max": "now"}, "field": "time", "fixed_interval": interval} }} }}}
    
    if interval != "1d":
        body["aggs"]["warns"]["aggs"]["warns_true"]["date_histogram"]["extended_bounds"]["min"] = f"now-{minutes_since}m"

    if server != "ALL":
        body["query"]["bool"]["must"].append({"match": {"server": server}})

    resp = es.search(index="logs", body=body)
    try:
        emit("API:GET_WARNS_COUNT", {'status': 1, 'items': resp['aggregations']['warns']['buckets'][1]["warns_true"]['buckets']})
    except Exception as e:
        emit("API:GET_WARNS_COUNT", {'status': 1, 'items': []})

@app.route("/", methods=["GET"])
def main():
    return render_template("index.html", servers=os.listdir("logs"))

if __name__ == "__main__":
    es.indices.delete(index="logs")  
    
    create_index(es)
    time.sleep(1)
    
    serverUpdater(app, socketio)
    app.run(host="0.0.0.0", port=80)


