# weewx_skin
customized weewx
Using daemon code and instructions from here: http://blog.scphillips.com/posts/2013/07/getting-a-python-script-to-run-in-the-background-as-a-service-on-boot/
Replacement thermometer hardware and software is documented here: https://hackaday.io/project/101680-solar-powered-wifi-temperature-sensor-for-weewx/details
Earthquake map from: https://leafletjs.com/examples/quick-start/

extra_temp.py goes in /home/pi. It's the script that creates the text file with the temp in it.
extra_temp_service.py is the weewx service that reads it

this.py goes in /usr/share/weewx/user
It drives the On this Date in 2019 high/low/rain. It is a search extension and goes in the user directory under where the executables are. It's a terrible name, agreed.

extensions:Forecast, NWS forecast
Forecast needs Xtide (sudo apt-get install xtide)
https://github.com/chaunceygardiner/weewx-forecast
https://github.com/chaunceygardiner/weewx-nws
