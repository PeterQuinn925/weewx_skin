import syslog
import weewx
import time
import os

from weewx.wxengine import StdService

class extraTService(StdService):
    def __init__(self, engine, config_dict):
        super(extraTService, self).__init__(engine, config_dict)      
        d = config_dict.get('extraTService', {})
        self.filename = d.get('filename', '/var/tmp/extra_temp.txt')
        syslog.syslog(syslog.LOG_INFO, "extratemp: using %s" % self.filename)
        self.bind(weewx.NEW_ARCHIVE_RECORD, self.read_file)
    
    def read_file(self, event):
        try:
            with open(self.filename) as f:
                value = f.read()
            syslog.syslog(syslog.LOG_DEBUG, "extratemp: found value of %s" % value)
	    #skip it if it's stale. Acurite Driver will be used instead
            if time.time() - os.path.getmtime("/var/tmp/extra_temp.txt") < 1200: #20minutes
               event.record['outTemp'] = float(value)
        except Exception, e:
            syslog.syslog(syslog.LOG_ERR, "extratemp: cannot read value: %s" % e)
