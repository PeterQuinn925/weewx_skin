#!/usr/bin/env python3
import socket
from shutil import copyfile

#raspi2b is 10.0.0.20 Raspi3 is 10.0.0.23
#UDP_IP = "10.0.0.9"
UDP_IP = "10.0.0.20"
UDP_PORT = 1026
fname = "/var/tmp/inTemp.txt"

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))


while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    print ("received message:", data)
    f = open(fname,'w')
    f.write(data.decode('utf-8'))
    f.write('\n')
    f.close()
    old_data = data
