#!/usr/bin/env python3
#import socket
from shutil import copyfile
import sys
import datetime
import time
import paho.mqtt.client as mqttClient
import json
import os

#generalized version on inTemp.py, extra_temp.py that uses MQTT with the argument the topic
# usage
# MQTT_sensor topic

#raspi2b is 10.0.0.20 Raspi3 is 10.0.0.23
#UDP_IP = "10.0.0.9"
#UDP_IP = "10.0.0.20"
# subtopic is aqi for air quality, pooltemp for pool thermomoter
subtopic = str(sys.argv[1])
fname = "/var/tmp/"+subtopic

# no longer using sockets or UDP - remove after testing
#sock = socket.socket(socket.AF_INET, # Internet
#                     socket.SOCK_DGRAM) # UDP
#sock.bind((UDP_IP, UDP_PORT))

def on_message(client, userdata, message):
#    print("message received " ,str(message.payload.decode("utf-8")))
#    print("message topic=",message.topic)
#    print("message qos=",message.qos)
#    print("message retain flag=",message.retain)
    mqtt_msg = json.loads(message.payload)
    outputlist =  []
    for m in mqtt_msg:
       print (mqtt_msg[m])
       outputlist.append(mqtt_msg[m])
    output = tuple(outputlist)
    print ("received message:", mqtt_msg)
    print (str(output))
    f = open(fname,'w')
    f.write(str(output))
    f.write('\n')
    f.close()

Connected = False
broker_address= "10.0.0.11" #Raspi4
port = 1883
topic = "weather/"+subtopic
clientname= "Raspi4_" + str(os.getpid()) #to make sure it's unique when it restarts
client = mqttClient.Client(clientname)
client.on_message=on_message
client.connect(broker_address,port=port)
#client.loop_forever()
client.subscribe(topic)
client.loop_forever(timeout=1.0, max_packets=1, retry_first_connection=False)
