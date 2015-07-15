import pycouchdb
import os
import json

#Couchdb setup
server = pycouchdb.Server("http://%s:%s@couch:5984/" %
                          (os.environ["SFMCOUCH_1_ENV_COUCHDB_USERNAME"],
                           os.environ["SFMCOUCH_1_ENV_COUCHDB_PASSWORD"]))

print "Creating dbs"
#Create warc_db
if "warc" not in server:
    warc_db = server.create("warc")
else:
    warc_db = server.database("warc")

#Create api_calls db
if "api_call" not in server:
    server.create("api_call")

#Create collection db
if "collection" not in server:
    server.create("collection")

print "Loading design docs"
with open("couch_design/warc.json") as f:
    warc_design_doc = json.load(f)
if "_design/warc" in warc_db:
    prev_warc_design_doc = warc_db.get("_design/warc")
    warc_design_doc["_rev"] = prev_warc_design_doc["_rev"]
warc_db.save(warc_design_doc)