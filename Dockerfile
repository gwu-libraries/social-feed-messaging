FROM python:2.7
MAINTAINER Justin Littman <justinlittman@gwu.edu>

RUN pip install --upgrade pip
ADD requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
WORKDIR /usr/local/social-feed-messaging
CMD pip install -r requirements.txt && /bin/bash