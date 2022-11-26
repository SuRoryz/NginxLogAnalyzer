from elasticsearch import Elasticsearch

es = Elasticsearch('https://elastic:OuOMugfLxanihRsaGWaX@localhost:9200', ca_certs="C:\\Users\\ri4ka\\Desktop\\sa\\config\\certs\\http_ca.crt")

def create_index(client):
    client.indices.create(
        index="logs",
        body={
            "settings": {"number_of_shards": 1},
            "mappings": {
                "properties": {
                    "remote_addr": {"type": "keyword"},
                    "remote_user": {"type": "text"},
                    "time": {"type": "date"},
                    "request_method": {"type": "keyword"},
                    "request_url": {"type": "keyword"},
                    "resuest_protocol": {"type": "keyword"},
                    "request_status": {"type": "keyword"},
                    "request_size": {"type": "integer"},
                    "http_reffer": {"type": "text"},
                    "user_agent": {"type": "text"},
                    "warn": {"type": "boolean"},
                    "server": {"type": "keyword"}
                }
            },
        },
        ignore=400,
    )