import pika
from random_words import RandomNicknames, RandomWords
import argparse
import time
import random

#Fake_scheduler submits harvest job requests.
#For faking purposes, it only submits flickr_user seeds.

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()

rw = RandomWords()
rn = RandomNicknames()

collections = ("isis", "washingtonia", "gwu")


def send_harvest_job():
    collection = random.choice(collections)

    body = """
    {
        "job": {
            "type": "harvest",
            "id": "harvest_%s_%s"
        },
        "collection": {
            "id": "%s_collection",
            "path": "/data/%s_collection"

        },
        "seeds": [
            {
                "type": "flickr_user",
                "username": "%s.%s"
            }
        ],
        "auths": {
            "flickr": {
                "key": "abddfefb88bba36e8ef0278ec65dbbc8",
                "secret": "164269c514cc3ebe"
            }
        },
        "fetch_strategy": {
            "depth2_resource_types": [
                "FlickrType"
            ],
            "depth3_resource_types": [
                "ImageType"
            ]
        }
    }
    """ % (collection, time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), collection, collection,
           rn.random_nick(gender="u"), rw.random_word().capitalize())

    print "Sending message to sfm_exchange with routing_key harvest_job. The body is: %s" % body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='job.harvest',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=body)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("num_msgs", type=int, default=1, nargs="?", help="Number of harvest job messages to send.")

    args = parser.parse_args()

    for i in range(0, args.num_msgs):
        print "Harvest job %s" % (i + 1)
        send_harvest_job()