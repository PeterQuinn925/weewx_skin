#!/usr/bin/python

# Using https://leafletjs.com/examples/quick-start/

import os
import urllib2
import subprocess
import json
import time
import datetime

latitude = 37.89
longitude = -122.05
earthquake_maxradiuskm = 300
earthquake_stale_timer = 600 #60 sec for now, increase to 600 later
n_quakes = 10 #max number of quakes to list

earthquake_url = "http://earthquake.usgs.gov/fdsnws/event/1/query?limit=%s&lat=%s&lon=%s&maxradiuskm=%s&format=geojson&nodata=204&minmag=2" % ( n_quakes, latitude, longitude, earthquake_maxradiuskm )

if os.name == "nt": #running on windows
   earthquake_file = "c:\Users\peter\earthquake.json"
   html_file = "c:\users\peter\earthquake.html"
else:
   earthquake_file = "/var/tmp/earthquake.json"
   html_file = "/var/www/weewx/earthquake.html"

while True:
   if os.path.isfile( earthquake_file ): #no need to check if stale since it sleeps
#       if ( int( time.time() ) - int( os.path.getmtime( earthquake_file ) ) ) > int( earthquake_stale_timer ):
#           earthquake_is_stale = True
#       else:
   # File doesn't exist, download a new copy
          earthquake_is_stale = True

   # File is stale, download a new copy
   if earthquake_is_stale:
   # Download new earthquake data
       try:
           user_agent = 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.3 (KHTML, like Gecko) Chrome/6.0.472.63 Safari/534.3'
           headers = { 'User-Agent' : user_agent }
           req = urllib2.Request( earthquake_url, None, headers )
           response = urllib2.urlopen( req )
           page = response.read()
           response.close()
       except Exception as error:
           # Nested try - only execute if the urllib2 method fails
           try:
               command = 'curl -L --silent "%s"' % earthquake_url
               p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
               page = p.communicate()[0]
           except Exception as error:
               raise Warning( "Error downloading earthquake data using urllib2 and subprocess curl. Your software may need to be updated, or the URL is incorrect. You are trying to use URL: %s, and the error is: %s" % ( earthquake_url, error ) )

       # Save earthquake data to file. w+ creates the file if it doesn't exist, and truncates the file and re-writes it everytime
       try:
           with open( earthquake_file, 'w+' ) as file:
               file.write( page )
       except IOError, e:
           raise Warning( "Error writing earthquake data to %s. Reason: %s" % ( earthquake_file, e) )
              # Process the earthquake file
       with open( earthquake_file, "r" ) as read_file:
              eqdata = json.load( read_file )
# create HTML
       try:
           with open( html_file, 'w+' ) as file:
               file.write('<div id ="earthquake"\n')
               file.write('style = "width: 350px;"\n')
               file.write('class="quake_data">\n')
# loop through and write text
               eqtime = []
               eqtime_datetime = []
               equrl = []
               eqplace = []
               eqmag= []
               eqlat = []
               eqlon = []
               for i in range(0,n_quakes):
                   temp_time_t = datetime.datetime.strptime(time.ctime(eqdata["features"][i]["properties"]["time"]/1000),"%a %b %d %H:%M:%S %Y")
                   temp_time_s = temp_time_t.strftime("%m-%d %I:%M %p")
                   eqtime.append(temp_time_s)
                   eqtime_datetime.append(temp_time_t)
                   equrl.append(eqdata["features"][i]["properties"]["url"])
                   eqplace.append(eqdata["features"][i]["properties"]["place"])
                   eqmag.append(eqdata["features"][i]["properties"]["mag"])
                   eqlat.append(str(round( eqdata["features"][i]["geometry"]["coordinates"][0], 4 ) ))
                   eqlon.append(str(round( eqdata["features"][i]["geometry"]["coordinates"][1], 4 ) ))
                   file.write("<br>%s  %5.2f   %s\n" % (eqtime[i], eqmag[i], eqplace[i]))
               file.write('</div>')
               file.write('<script>')
               file.write("var mymap = L.map('mapid').setView([37.89, -122.05], 8);\n")
#L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {
#attribution: 'Map data &copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a> contributors, <a href="https://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>, Imagery  <a href="https://www.mapbox.com/">Mapbox</a>',
#maxZoom: 18,
#id: 'mapbox.streets',
#accessToken: 'pk.eyJ1IjoicGV0ZXJxdWlubjkyNSIsImEiOiJjazFmaGN2aW0wdHBxM2dxbzViN3l5dTRkIn0.jsrb9kj1DH_pa_GWc8rKYA'
#}).addTo(mymap);
               file.write("L.tileLayer('https://api.tiles.mapbox.com/v4/{id}/{z}/{x}/{y}.png?access_token={accessToken}', {\n")
               file.write("attribution: 'Map data &copy; <a href=\"https://www.openstreetmap.org/\">OpenStreetMap</a> contributors, <a href=\"https://creativecommons.org/licenses/by-sa/2.0/\">CC-BY-SA</a>, ")
               file.write("Imagery  <a href=\"https://www.mapbox.com/\">Mapbox</a>',")
               file.write("maxZoom: 18,id: 'mapbox.streets',\n")
               file.write("accessToken: 'pk.eyJ1IjoicGV0ZXJxdWlubjkyNSIsImEiOiJjazFmaGN2aW0wdHBxM2dxbzViN3l5dTRkIn0.jsrb9kj1DH_pa_GWc8rKYA'")
               file.write("}).addTo(mymap);\n")
#loop and put circles on the map for each quake
# roygbv purple in the last 20 minutes, blue if the last hr, green if last 4 hrs, yellow if older
               for i in range(0,n_quakes):
                  tdelta = datetime.datetime.now() - eqtime_datetime[i]
                  timediff = tdelta.total_seconds() /60
                  if timediff <20:
                     eq_color = "#660000"
                  elif timediff < 60:
                     eq_color = "#990000"
                  elif timediff <60*4:
                     eq_color = "#ff0000"
                  else:
                     eq_color = "#ff6666"

                  file.write('var circle = L.circle([' + eqlon[i] + ',' + eqlat[i] + '], {\n')
                  file.write('color: "' + eq_color + '", fillColor: "' + eq_color + '", radius: ' + str(300*eqmag[i]) + '}).addTo(mymap);\n')
                  file.write('circle.bindPopup("%5.2f   %s");\n' % (eqmag[i], eqplace[i]))
               file.write('</script>\n')
               file.close();
#var circle = L.circle([37.88,-122.057], {
#  color: "red", fillColor: '#f03', radius: 500}).addTo(mymap);

       except IOError, e:
           raise Warning( "Error writing earthquake data to %s. Reason: %s" % ( earthquake_file, e) )
       time.sleep(earthquake_stale_timer)
