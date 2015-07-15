import pycouchdb
import os
import json
import pika
import argparse

#RabbitMQ setup
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()

#Couchdb setup
server = pycouchdb.Server("http://%s:%s@couch:5984/" %
                          (os.environ["SFMCOUCH_1_ENV_COUCHDB_USERNAME"],
                           os.environ["SFMCOUCH_1_ENV_COUCHDB_PASSWORD"]))
warc_db = server.database("warc")
collection_db = server.database("collection")

#Get map of collection_ids to paths
collections = {}
for coll_res in collection_db.all():
    collections[coll_res["id"]] = coll_res["doc"]["path"]


def republish_warc_created(collection_id, service_name):
    # Republish warc created messages for a particular collection.
    print "Republishing warc_created messages for collection %s to service %s" % (collection_id, service_name)

    for res in warc_db.query("warc/collectionid", key=collection_id, include_docs=True):
        collection_id = res["doc"]["collection_id"]
        warc_created_body = {
            "collection": {
                "id": collection_id,
                "path": collections[collection_id]

            },
            "warc": {
                "id": res["doc"]["warc_id"],
                "path": res["doc"]["warc_id"],
                "created_date": res["doc"]["created_date"]
            }
        }
        routing_key = "warc_created.for_%s" % service_name
        warc_created_body = json.dumps(warc_created_body, indent=4)
        print "Sending message to sfm_exchange with routing_key %s. The body is: %s" % (
            routing_key, warc_created_body)
        channel.basic_publish(exchange='sfm_exchange',
                              routing_key=routing_key,
                              properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                              body=warc_created_body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser()

    #Using subparsers to allow for adding other republishing methods
    subparsers = parser.add_subparsers()
    parser_warc_created = subparsers.add_parser("warc_created", help="Republish warc created messages.")
    parser_warc_created.add_argument("collection_id")
    parser_warc_created.add_argument("service_name")
    parser_warc_created.set_defaults(func=republish_warc_created)

    args = parser.parse_args()
    args_map = vars(args).copy()
    del args_map["func"]
    args.func(**args_map)
