# weewx_skin
customized weewx

Replacement thermometer hardware and software is documented here: https://hackaday.io/project/101680-solar-powered-wifi-temperature-sensor-for-weewx/details
Earthquake map from: https://leafletjs.com/examples/quick-start/

this.py goes in /usr/share/weewx/user
It drives the On this Date in 2019 high/low/rain. It is a search extension and goes in the user directory under where the executables are. It's a terrible name, agreed.

extensions:Forecast, NWS forecast
Forecast needs Xtide (sudo apt-get install xtide)
https://github.com/chaunceygardiner/weewx-forecast
https://github.com/chaunceygardiner/weewx-nws

2/25/26 Removed additional sensor services. Now using exclusively MQTT.
