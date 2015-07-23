# social-feed-messaging
An SFM-related experiment with using messaging to couple a set of services / applications.

## Overview
For the experiment, RabbitMQ is used for to facilitate the exchange of messages between a set of (fake) services and applications.

### Services and applications
#### Scheduler
A real scheduler would publish harvest job messages according to a schedule.  A harvest job message states that a set of seeds (e.g., a twitter user timeline or a flickr user) should be harvested for a particular collection.  The fake scheduler just submits some number of random flickr seeds for a random choice from a set of collections.  It is invoked from the command line.  (That is, the fake scheduler does not actually schedule.)

#### Harvester
A real scheduler would consume harvest job messages, perform harvesting, and write the results to warc files.  It would also publish warc created messages, api harvested messages, and job result messages.  The fake harvester just consumes harvest job messages and for each harvest publishes a warc created message, an api harvested message for flickr people.getInfo, an api harvested message for flickr people.getPublicPhotos, and a job result message.  For the job result message, it is randomly selected whether to report the job succeeded, succeeded with messages, or failed.

#### Indexer
A real indexer would consume warc created messages, index the warc contents (e.g., into PyWb or ElasticSearch), and publish job result messages.  The fake indexer just consumes the warc created messages and publishes job result messages.

#### Model listener
The model listener consumes warc created messages and api harvested message and persists a model of the warcs, api harvests, and collections to the modeler service.

#### Modeler
Store of various models that can be used by other services (e.g., the republisher service or an access application).  For this experiment, the modeler is a CouchDb instance.

#### Republisher
The republisher will republish messages for management purposes.  For example, if a new indexer service is added, it may be necessary to republish previous warc created messages.  The republisher may query the modeler service to determine what messages to republish.  The fake republisher is invoked from the command line and only republishes warc created messages for a specified collection.

This is not intended to be a complete list of services / applications that would be necessary for SFM.  Examples of other services / applications might include:

* SFM UI application:
    * Allows users to create, update, and view collections and seed sets.
    * Models collections, seed sets, and job results.
    * Allows users to view job results.
    * Possible facade for other services, e.g., export.
* Analysis application:  Allows users to view analysis of harvested social media content (e.g., popular hashtags, links, or tags).
* Export service:  Supports export of social media content from warcs.
* Access application:  Allows users to provide harvested social media content, perhaps using data from the modeler or indexer services.

### Example messages
#### Harvest job message
    {
        "job": {
            "type": "harvest",
            "id": "harvest_isis_2015-07-15T15:22:42Z"
        },
        "collection": {
            "id": "isis_collection",
            "path": "/data/isis_collection"

        },
        "seeds": [
            {
                "type": "flickr_user",
                "username": "Eddie.Egg"
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

#### Job result message

		{
		    "auths": {
		        "flickr": {
		            "secret": "164269c514cc3ebe", 
		            "key": "abddfefb88bba36e8ef0278ec65dbbc8"
		        }
		    }, 
		    "fetch_strategy": {
		        "depth3_resource_types": [
		            "ImageType"
		        ], 
		        "depth2_resource_types": [
		            "FlickrType"
		        ]
		    }, 
		    "collection": {
		        "path": "/data/gwu_collection", 
		        "id": "gwu_collection"
		    }, 
		    "job": {
		        "type": "harvest", 
		        "id": "harvest_gwu_2015-07-15T15:22:42Z"
		    }, 
		    "seeds": [
		        {
		            "username": "Nina.Pushups", 
		            "type": "flickr_user"
		        }
		    ], 
		    "result": {
		        "errors": [
		            {
		                "message": "Something went really wrong", 
		                "code": "OOOPS"
		            }
		        ], 
		        "completed_date": "2015-07-15T15:26:32.867372", 
		        "success": false
		    }
		}

#### Warc created message

		{
		    "collection": {
		        "id": "isis_collection",
		        "path": "/data/isis_collection"

		    },
		    "warc": {
		        "id": "isis_collection-2015-07-15T15:26:52Z",
		        "path": "/data/isis_collection/2015/07/15/15/isis_collection-2015-07-15T15:26:52Z.warc.gz",
		        "created_date": "2015-07-15T15:26:52.894947"
		    }

		}


#### Api harvested message

		{
		    "collection": {
		        "id": "isis_collection",
		        "path": "/data/isis_collection"

		    },
		    "api": {
		        "service": "flickr",
		        "method": "people.getPublicPhotos",
		        "parameters": {
		            "nsid": "accruement",
		            "format": "parsed-json"
		        },
		        "other_parameters": {
		            "username":  "Wendell.Certifications"
		        },
		        "harvested_date": "2015-07-15T15:26:42.879736"
		    },
		    "warc": {
		        "id": "isis_collection-2015-07-15T15:26:42Z",
		        "path": "/data/isis_collection/2015/07/15/15/isis_collection-2015-07-15T15:26:42Z.warc.gz"
		    }

		}

## Give it a try

### Bring up containers

1.  Install docker (or boot2docker for OS X) and docker-compose.
2.  Clone this repo.
3.  Change the volumes configuration in docker-compose.yml to point to your cloned repo:

                    volumes:
                        - "~/Data/social-feed-messaging:/usr/local/social-feed-messaging"
                        
    Note that there are multiple instances of the volumes configuration.
4.  Bring up the containers:

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker-compose up -d
		Creating socialfeedmessaging_sfmcouch_1...
		Creating socialfeedmessaging_sfmrabbit_1...
		Creating socialfeedmessaging_sfmscheduler_1...
		Creating socialfeedmessaging_sfmmodellistener_1...
		Creating socialfeedmessaging_sfmindexer_1...
		Creating socialfeedmessaging_sfmharvester_1...

5.  If you want to add multiple instance of the harvester service:

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker-compose scale sfmharvester=2
		Starting socialfeedmessaging_sfmharvester_2...


### Start some harvests
Tell the scheduler to request some harvest jobs:

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker exec -it socialfeedmessaging_sfmscheduler_1 /bin/bash
		root@0316663d493e:/usr/local/social-feed-messaging# python fake_scheduler.py 5

### Observe

#### Observe all containers

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker-compose logs

#### Observe a single container
(using `docker ps` to get a list of container names):

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker logs socialfeedmessaging_sfmharvester_1

#### Observe RabbitMQ

http://[localhost or `boot2docker ip`]:8081/ (The username and password are "guest".)


#### Observe CouchDB:

http://[localhost or `boot2docker ip`]:5984/_utils/ (The username is "sfmuser" and password is "password".)


### Republish some warc created messages

		GLSS-F0G5RP:social-feed-messaging justinlittman$ docker exec -it socialfeedmessaging_sfmmodellistener_1 /bin/bash
		root@cbf98ed17191:/usr/local/social-feed-messaging# python republisher.py -h
		usage: republisher.py [-h] {warc_created} ...

		positional arguments:
		  {warc_created}
		    warc_created  Republish warc created messages.

		optional arguments:
		  -h, --help      show this help message and exit
		root@cbf98ed17191:/usr/local/social-feed-messaging# python republisher.py warc_created isis_collection indexer


### Tear down your containers

```
GLSS-F0G5RP:social-feed-messaging justinlittman$ docker-compose kill
Killing socialfeedmessaging_sfmharvester_1...
Killing socialfeedmessaging_sfmindexer_1...
Killing socialfeedmessaging_sfmmodellistener_1...
Killing socialfeedmessaging_sfmscheduler_1...
Killing socialfeedmessaging_sfmrabbit_1...
Killing socialfeedmessaging_sfmcouch_1...
GLSS-F0G5RP:social-feed-messaging justinlittman$ docker-compose rm -v --force
Going to remove socialfeedmessaging_sfmharvester_1, socialfeedmessaging_sfmindexer_1, socialfeedmessaging_sfmmodellistener_1, socialfeedmessaging_sfmscheduler_1, socialfeedmessaging_sfmrabbit_1, socialfeedmessaging_sfmcouch_1
Removing socialfeedmessaging_sfmcouch_1...
Removing socialfeedmessaging_sfmrabbit_1...
Removing socialfeedmessaging_sfmscheduler_1...
Removing socialfeedmessaging_sfmmodellistener_1...
Removing socialfeedmessaging_sfmindexer_1...
Removing socialfeedmessaging_sfmharvester_1...
```
