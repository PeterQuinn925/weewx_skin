#!/usr/bin/env python
import socket
from shutil import copyfile

UDP_IP = "10.0.0.20"
UDP_PORT = 1025
fname = "/var/tmp/extra_temp.txt"

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))


while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print "received message:", data
    f = open(fname,'w')
    f.write(data)
    f.write('\n')
    f.close()
    old_data = data
