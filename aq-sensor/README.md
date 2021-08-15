This is the script that runs on raspi that controls a SDS011 air quality sensor and sends it to the machine that hosts weewx.
There's a separate script on the weewx machine that listens to this port and writes the data to a file for the custom weewx driver to pick up.
This uses a python aqi library and a python dsd011 library that need to be installed
