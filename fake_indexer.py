import pika
import time
import json
from random import randint
from random_words import RandomWords

#Fake_indexer pretends to index WARCs.
#Fake_indexer consumers warc_created messages.
#It submits job result messages.

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()

def callback(ch, method, properties, body):
    print "Received message with routing_key %s. The body is: %s" % (method.routing_key, body)
    #Acknowledge the message
    ch.basic_ack(delivery_tag=method.delivery_tag)

    index_job = json.loads(body)

    print "Fake indexing %s" % index_job["warc"]["id"]

    #Now let's wait a few seconds
    time.sleep(10)

    #Add job info
    index_job["job"] = {
        "type": "index",
        "id": "index_%s_%s" % (index_job["collection"]["id"], time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    }

    #Let's decide if we succeeded
    result = randint(0,9)
    if result == 0:
        index_job["result"] = {
            "success": False,
            "errors": [
                {"code": "OOOPS",
                 "message": "Something went really wrong"}
            ]
        }
    else:
        #Succeeded
        index_job["result"] = {
            "success": True
        }
    harvest_job_result_body = json.dumps(index_job, indent=4)
    print "Sending message to sfm_exchange with harvest_job_result. The body is: %s" % harvest_job_result_body
    channel.basic_publish(exchange='sfm_exchange',
                          routing_key='job_result.index',
                          properties=pika.spec.BasicProperties(content_type="application/json", delivery_mode=2),
                          body=harvest_job_result_body)


if __name__ == '__main__':
    channel.basic_qos(prefetch_count=1)
    print "Waiting for warc_created messages"
    channel.basic_consume(callback,
                          queue="indexer")
    channel.start_consuming()
