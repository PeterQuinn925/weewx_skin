#!/usr/bin/env python3
from sds011 import SDS011
import socket
import time
import aqi

UDP_IP = "10.0.0.20"
UDP_PORT = 1027
sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sensor=SDS011("/dev/ttyUSB0",use_query_mode=True)
while True:
   sensor.sleep(sleep=False)
   time.sleep(30)
   data = sensor.query()
   #convert to AQI from micrograms/m^3
   aqi_2_5=aqi.to_iaqi(aqi.POLLUTANT_PM25, str(data[0]))
   aqi_10=aqi.to_iaqi(aqi.POLLUTANT_PM10, str(data[1]))
   aqi_data = (str(aqi_2_5).encode('utf-8'),str(aqi_10).encode('utf-8'))
   print(data)
   print(aqi_data)
   sensor.sleep()
#   sock.sendto(str(data.encode('utf-8')), (UDP_IP,UDP_PORT))
   sock.sendto(str(aqi_data).encode('utf-8'), (UDP_IP,UDP_PORT))
   time.sleep(300)
