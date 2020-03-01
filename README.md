# weewx_skin
customized weewx
Using daemon code and instructions from here: http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
Replacement thermometer hardware and software is documented here: https://hackaday.io/project/101680-solar-powered-wifi-temperature-sensor-for-weewx/details
Earthquake map from: https://leafletjs.com/examples/quick-start/

extra_temp.py goes in /home/pi. It's the script that creates the text file with the temp in it.
extra_temp_service.py is the weewx service that reads it
