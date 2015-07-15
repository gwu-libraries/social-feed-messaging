import pika
import json
import pycouchdb
import os

#Fake_model_listener loads the social feed modeler.
#Fake_model_listener consumes warc_created messages.

#Pika setup
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()

#Couchdb setup
server = pycouchdb.Server("http://%s:%s@couch:5984/" %
                          (os.environ["SFMCOUCH_1_ENV_COUCHDB_USERNAME"],
                           os.environ["SFMCOUCH_1_ENV_COUCHDB_PASSWORD"]))
warc_db = server.database("warc")
api_call_db = server.database("api_call")
collection_db = server.database("collection")

def callback(ch, method, properties, body):
    print "Received message with routing_key %s. The body is: %s" % (method.routing_key, body)
    #Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

    msg = json.loads(body)
    collection_id = msg["collection"]["id"]

    payload = None
    entity = None
    if method.routing_key == 'warc_created':
        print "Adding warc %s to modeler" % (msg["warc"]["id"])
        warc_db.save({
            "warc_id": msg["warc"]["id"],
            "path": msg["warc"]["path"],
            "collection_id": collection_id,
            "created_date": msg["warc"]["created_date"]
        })
    elif method.routing_key == 'api_harvested':
        print "Adding api call %s->%s to modeler" % (msg["api"]["service"], msg["api"]["method"])
        api_call_db.save({
            "service": msg["api"]["service"],
            "method": msg["api"]["method"],
            "collection_id": collection_id,
            "harvested_date": msg["api"]["harvested_date"],
            "warc_id": msg["warc"]["id"],
            "parameters": msg["api"]["parameters"],
            "other_parameters": msg["api"].get("other_parameters", {})
        })
    #Add/update collection
    collection_path = msg["collection"]["path"]
    collection_doc = None
    if collection_id in collection_db:
        prev_collection_doc = collection_db.get(collection_id)
        #If path has changed, then update
        if prev_collection_doc["path"] != collection_path:
            collection_doc = prev_collection_doc
            collection_doc["path"] = collection_path
        #Otherwise, do nothing
    else:
        collection_doc = {
            "_id": collection_id,
            "path": collection_path
        }
    if collection_doc:
        print "Adding/updating collection %s in modeler" % collection_id
        collection_db.save(collection_doc)


if __name__ == '__main__':
    channel.basic_qos(prefetch_count=1)
    print "Waiting for messages"
    channel.basic_consume(callback,
                          queue="model_listener")
    channel.start_consuming()
