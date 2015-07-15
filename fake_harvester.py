import pika
import time
import json
from random import randint
from random_words import RandomWords
from datetime import datetime

#Fake_harvester pretends to perform harvesting from APIs.
#Fake_harvester consumes harvest job messages.
#For faking purposes, it only handles flickr_user seeds.
#It submits api_harvested, warc_created, and job result messages.

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()
rw = RandomWords()


def generate_warc_filepath(collection_path, collection_id):
    t = time.gmtime()
    return "%s/%s/%s/%s/%s/%s-%s.warc.gz" % (
        collection_path,
        time.strftime('%Y', t),
        time.strftime('%m', t),
        time.strftime('%d', t),
        time.strftime('%H', t),
        collection_id,
        time.strftime('%Y-%m-%dT%H:%M:%SZ', t)
    )


def callback(ch, method, properties, body):
    print "Received message with routing_key %s. The body is: %s" % (method.routing_key, body)
    #Acknowledge the message
    ch.basic_ack(delivery_tag = method.delivery_tag)
    harvest_job = json.loads(body)
    collection_id = harvest_job["collection"]["id"]
    collection_path = harvest_job["collection"]["path"]
    seed_type = harvest_job["seeds"][0]["type"]
    username = harvest_job["seeds"][0]["username"]

    print "Fake harvesting %s (%s) for collection %s" % (seed_type, username, collection_id)

    #Now let's wait a few seconds
    time.sleep(10)


    t = time.gmtime()
    warc_id = "%s-%s" % (collection_id, time.strftime('%Y-%m-%dT%H:%M:%SZ', t))
    warc_path = "%s/%s/%s/%s/%s/%s.warc.gz" % (
        collection_path,
        time.strftime('%Y', t),
        time.strftime('%m', t),
        time.strftime('%d', t),
        time.strftime('%H', t),
        warc_id)

    #Let's pretend people.getInfo() was called.
    api_harvested_body = """
{
    "collection": {
        "id": "%s",
        "path": "%s"

    },
    "api": {
        "service": "flickr",
        "method": "people.getInfo",
        "parameters": {
            "nsid": "%s"
        },
        "other_parameters": {
            "username":  "%s"
        },
        "harvested_date": "%s"
    },
    "warc": {
        "id": "%s",
        "path": "%s"
    }

}
    """ % (collection_id, collection_path, rw.random_word(), username,
           datetime.now().isoformat(), warc_id, warc_path)
    print "Sending message to sfm_exchange with routing_key api_harvested. The body is: %s" % api_harvested_body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='api_harvested',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=api_harvested_body)

    #And people.getPublicPhotos()
    api_harvested_body = """
{
    "collection": {
        "id": "%s",
        "path": "%s"

    },
    "api": {
        "service": "flickr",
        "method": "people.getPublicPhotos",
        "parameters": {
            "nsid": "%s",
            "format": "parsed-json"
        },
        "other_parameters": {
            "username":  "%s"
        },
        "harvested_date": "%s"
    },
    "warc": {
        "id": "%s",
        "path": "%s"
    }

}
    """ % (collection_id, collection_path, rw.random_word(), username, datetime.now().isoformat(), warc_id, warc_path)
    print "Sending message to sfm_exchange with routing_key api_harvested. The body is: %s" % api_harvested_body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='api_harvested',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=api_harvested_body)

    #Report that a warc was created.
    warc_created_body = """
{
    "collection": {
        "id": "%s",
        "path": "%s"

    },
    "warc": {
        "id": "%s",
        "path": "%s",
        "created_date": "%s"
    }

}

    """ % (collection_id, collection_path, warc_id, warc_path, datetime.now().isoformat())
    print "Sending message to sfm_exchange with routing_key warc_created. The body is: %s" % warc_created_body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='warc_created',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=warc_created_body)

    #Let's decide if we succeeded
    result = randint(0,9)
    if result == 0:
        harvest_job["result"] = {
            "success": False,
            "errors": [
                {"code": "OOOPS",
                 "message": "Something went really wrong"}
            ]
        }
    elif result == 1 or result == 2:
        #Passed with message
        harvest_job["result"] = {
            "success": False,
            "warnings": [
                {"code": "FLICKR_CHANGE_USERNAME",
                 "message": "The Flickr username changed."}
            ]
        }

    else:
        #Succeeded
        harvest_job["result"] = {
            "success": True
        }
    harvest_job["result"]["completed_date"] = datetime.now().isoformat()
    harvest_job_result_body = json.dumps(harvest_job, indent=4)
    print "Sending message to sfm_exchange with harvest_job_result. The body is: %s" % harvest_job_result_body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='job_result.harvest',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=harvest_job_result_body)


if __name__ == '__main__':
    channel.basic_qos(prefetch_count=1)
    print "Waiting for job.harvest messages"
    channel.basic_consume(callback,
                          queue="harvester")
    channel.start_consuming()
