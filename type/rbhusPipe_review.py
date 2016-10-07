#!/usr/bin/env python2
#-*- coding: utf-8 -*-
__author__ = "Shrinidhi Rao"
__license__ = "GPL"
__email__ = "shrinidhi666@gmail.com"

import zmq
import uuid
import time
import sys
import simplejson
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-a","--assetpath",dest='assPath',required=True,help='asset path')
parser.add_argument("-p","--project",dest='project',required=True,help='asset path')
args = parser.parse_args()

message_str = {
               "test":"testing",
               "project":args.project,
               "asset":args.assPath,
               "run":"review"
               }
message = simplejson.dumps(message_str)
ip = "127.0.0.1"
port = 8989
context = zmq.Context()
request_id = uuid.uuid4()

socket = context.socket(zmq.REQ)
socket.connect("tcp://{0}:{1}".format(ip, port))
socket.poll(timeout=1)
poller = zmq.Poller()
poller.register(socket, zmq.POLLIN)
print ("Sending request {0} …".format(request_id))
# send_msg = self.process(message)
timestarted = time.time()

socket.send_multipart([bytes(request_id),bytes(message)])
while(True):
  sockets = dict(poller.poll(10000))
  if(sockets):
    for s in sockets.keys():
      if(sockets[s] == zmq.POLLIN):
        try:
          (recv_id, recved_msg) = s.recv_multipart()
          # recv_message = self.process(recved_msg)
        except:
          print (sys.exc_info())
        break
    break
  print ("Reciever Timeout error : Check if the server is running")


print ("Received reply %s : %s [ %s ]" % (recv_id,recved_msg, time.time() - timestarted))
socket.close()