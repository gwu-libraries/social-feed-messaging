import pika

#Declares all exchanges, queues, and bindings.

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbit"))
channel = connection.channel()

#Declare sfm_exchange
print "Declaring exchange"
channel.exchange_declare(exchange="sfm_exchange",
                         type="topic", durable=True)

#Each service that consumes messages needs a queue
print "Declaring queues"
#Harvester
channel.queue_declare(queue="harvester",
                      durable=True)
channel.queue_bind(exchange='sfm_exchange',
                   queue="harvester",
                   routing_key="job.harvest")
#This allows sending job.harvest messages directly to harvester
channel.queue_bind(exchange='sfm_exchange',
                   queue="harvester",
                   routing_key="job.harvest.for_harvester")

#Indexer
channel.queue_declare(queue="indexer",
                      durable=True)
channel.queue_bind(exchange='sfm_exchange',
                   queue="indexer",
                   routing_key="warc_created")
#This allows sending warc_created messages directly to indexer
channel.queue_bind(exchange='sfm_exchange',
                   queue="indexer",
                   routing_key="warc_created.for_indexer")

#Model listener
channel.queue_declare(queue="model_listener",
                      durable=True)
channel.queue_bind(exchange='sfm_exchange',
                   queue="model_listener",
                   routing_key="warc_created")
#This allows sending warc_created messages directly to model_listener
channel.queue_bind(exchange='sfm_exchange',
                   queue="model_listener",
                   routing_key="warc_created.for_model_listener")
channel.queue_bind(exchange='sfm_exchange',
                   queue="model_listener",
                   routing_key="api_harvested")
#This allows sending api_harvested messages directly to model_listener
channel.queue_bind(exchange='sfm_exchange',
                   queue="model_listener",
                   routing_key="api_harvested.for_model_listener")


connection.close()