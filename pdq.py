#!/usr/bin/env python
#
# ******Removed most, if not all, of Acurite functionality as the USB interface has become unreliable with recent versions of Linux

from __future__ import with_statement
from __future__ import absolute_import
from __future__ import print_function

import logging
import time
# import usb  remove usb so that errors are apparent
import os
import subprocess

import weewx.drivers
import weewx.wxformulas
from weeutil.weeutil import to_bool

log = logging.getLogger(__name__)

DRIVER_NAME = 'AcuRite'
DRIVER_VERSION = '0.4'
DEBUG_RAW = 0

# USB constants for HID
#USB_HID_GET_REPORT = 0x01
#USB_HID_SET_REPORT = 0x09
#USB_HID_INPUT_REPORT = 0x0100
#USB_HID_OUTPUT_REPORT = 0x0200

def loader(config_dict, engine):
    return AcuRiteDriver(**config_dict[DRIVER_NAME])

def confeditor_loader():
    return AcuRiteConfEditor()

def _fmt_bytes(data):
    return ' '.join(['%02x' % x for x in data])


class AcuRiteDriver(weewx.drivers.AbstractDevice):
#This used to be the driver for Acurite, but all of the acurite stuff has been removed and replaced with custom sensors

    def __init__(self, **stn_dict):
        log.info('driver version is %s' % DRIVER_VERSION)
        self.model = stn_dict.get('model', 'AcuRite')
        self.max_tries = int(stn_dict.get('max_tries', 10))
        self.retry_wait = int(stn_dict.get('retry_wait', 30))
        self.polling_interval = int(stn_dict.get('polling_interval', 6))
        self.use_constants = to_bool(stn_dict.get('use_constants', True))
        self.ignore_bounds = to_bool(stn_dict.get('ignore_bounds', False))
        self.last_rain = None
        self.last_r3 = None
        self.r3_fail_count = 0
        self.r3_max_fail = 3
        self.r1_next_read = 0
        self.r2_next_read = 0
        global DEBUG_RAW
        DEBUG_RAW = int(stn_dict.get('debug_raw', 0))

    @property
    def hardware_name(self):
        return self.model

    def genLoopPackets(self):
        last_raw2 = None
        ntries = 0
        while ntries < self.max_tries:
            ntries += 1
            try:
                packet = {'dateTime': int(time.time() + 0.5),
                          'usUnits': weewx.METRIC}
                raw1 = raw2 = None
                with Station() as station:
                    if time.time() >= self.r1_next_read:
                        raw1 = station.read_R1()
                        self.r1_next_read = time.time() + 20
                        if DEBUG_RAW > 0 and raw1:
                            log.debug("R1: %s" % _fmt_bytes(raw1))
                    if time.time() >= self.r2_next_read:
                        raw2 = station.read_R2()
                        self.r2_next_read = time.time() + 20
                        if DEBUG_RAW > 0 and raw2:
                            log.debug("R2: %s" % _fmt_bytes(raw2))
                if raw1:
                    packet.update(Station.decode_R1(raw1))
                if raw2:
                    last_raw2 = raw2
                    packet.update(Station.decode_R2(
                            raw2, self.use_constants, self.ignore_bounds))
                self._augment_packet(packet)
                ntries = 0
                yield packet
                next_read = min(self.r1_next_read, self.r2_next_read)
                delay = max(int(next_read - time.time() + 1),
                            self.polling_interval)
                log.debug("next read in %s seconds" % delay)
                time.sleep(delay)
            except (weewx.WeeWxIOError) as e:
                log.error("Failed attempt %d of %d to get LOOP data: %s" %
                          (ntries, self.max_tries, e))
                time.sleep(self.retry_wait)
        else:
            msg = "Max retries (%d) exceeded for LOOP data" % self.max_tries
            log.error(msg)
            raise weewx.RetriesExceeded(msg)

    def _augment_packet(self, packet):
        # calculate the rain delta from the total
        if 'rain_total' in packet:
            total = packet['rain_total']
            if (total is not None and self.last_rain is not None and
                total < self.last_rain):
                log.info("rain counter decrement ignored:"
                         " new: %s old: %s" % (total, self.last_rain))
            packet['rain'] = weewx.wxformulas.calculate_rain(total, self.last_rain)
            self.last_rain = total

        # if there is no connection to sensors, clear the readings
        if 'rssi' in packet and  packet['rssi'] == 0:
# pdq - changed outTemp to extraTemp1
#            packet['extraTemp1'] = None
            packet['outTemp'] = None
            packet['outHumidity'] = None
            packet['windSpeed'] = None
            packet['windDir'] = None
            packet['rain'] = None

        # map raw data to observations in the default database schema
        if 'sensor_battery' in packet:
            if packet['sensor_battery'] is not None:
                packet['outTempBatteryStatus'] = 1 if packet['sensor_battery'] else 0
            else:
                packet['outTempBatteryStatus'] = None
        if 'rssi' in packet and packet['rssi'] is not None:
            packet['rxCheckPercent'] = 100 * packet['rssi'] / Station.MAX_RSSI

    def read_R3_block(self, station):
        # attempt to read R3 every 12 minutes.  if the read fails multiple
        # times, make a single log message about enabling usb mode 3 then do
        # not try it again.
        #
        # when the station is not in mode 3, attempts to read R3 leave
        # it in an uncommunicative state.  doing a reset, close, then open
        # will sometimes, but not always, get communication started again on
        # 01036 stations.
        r3 = []
        if self.r3_fail_count >= self.r3_max_fail:
            return r3
        if (self.last_r3 is None or
            time.time() - self.last_r3 > self._R3_INTERVAL):
            try:
                x = station.read_x()
                for i in range(17):
                    r3.append(station.read_R3())
                self.last_r3 = time.time()
            except usb.USBError as e:
                self.r3_fail_count += 1
                log.debug("R3: read failed %d of %d: %s" %
                          (self.r3_fail_count, self.r3_max_fail, e))
                if self.r3_fail_count >= self.r3_max_fail:
                    log.info("R3: put station in USB mode 3 to enable R3 data")
        return r3


class Station(object):
    # these identify the weather station on the USB
    VENDOR_ID = 0x24c0
    PRODUCT_ID = 0x0003

    # map the raw wind direction index to degrees on the compass
    IDX_TO_DEG = {6: 0.0, 14: 22.5, 12: 45.0, 8: 67.5, 10: 90.0, 11: 112.5,
                  9: 135.0, 13: 157.5, 15: 180.0, 7: 202.5, 5: 225.0, 1: 247.5,
                  3: 270.0, 2: 292.5, 0: 315.0, 4: 337.5}

    # map the raw channel value to something we prefer
    # A is 1, B is 2, C is 3
    CHANNELS = {12: 1, 8: 2, 0: 3}

    # maximum value for the rssi
    MAX_RSSI = 3.0

    def __init__(self, vend_id=VENDOR_ID, prod_id=PRODUCT_ID, dev_id=None):
        self.vendor_id = vend_id
        self.product_id = prod_id
        self.device_id = dev_id
        self.handle = None
        self.timeout = 1000

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, _, value, traceback):
        self.close()

    def open(self):
        return True #nothing to do here anymore

    def close(self):
        return True #nothing to do here

    def read(self, report_number, nbytes):
        return True #emasculated

    def read_R1(self):
        return self.read(1, 10)

    def read_R2(self):
        return self.read(2, 25)

    def read_R3(self):
        return self.read(3, 33)

    def read_x(self):
        # removed all the guts here. There's nothing, per se, to read anymore 
        return True

    @staticmethod
    def decode_R1(raw):
        data = dict()
        try:
            #get the rain info from the file
            # json data {"worktime": float, "rainfall": float, "hourrain": float, "bucketcount": int}
            # file contains (worktime, rainfall, hourrain, bucketcount). We only need rainfall
            f=open('/var/tmp/rain')
            value= f.read()
            s = value.split(",") 
            raindata = s[1] #2nd value, which is the total
            data['rain_total']=(float(raindata)/25.4) #convert mm to inch
            f.close
        except:
            log.error("Can't read rain data")
            log.error(value)
        try:
            f=open('/var/tmp/extra_temp.txt')
            value = float(f.read())
            value = (value - 32) * 5/9 # convert to C
            data['outTemp']=value
            f.close()
        except:
            log.error("Can't read Extratemp")
        try:
            #get the internal temp and RH from the arduino 33 IoT device
            #10/7/23 pdq - change out ESP32 device for epaper nano iot with MQTT and remove .txt from filename
            #remove humdity. Didn't capture it in the new sensro - not interesting
            #2/10/26 pdq - add humidity back in
            f=open('/var/tmp/inTemp')
            value= f.read() #this will be in the format x,y where x is the temp and y is the RH
            inTempdata = value[1:-2].split(",")
            #inTempdata = value[1:-3] # used to be value.rsplit(",")
            data['extraTemp2']=(float(inTempdata[0])-32)*5/9 #convert to degC
            data['outHumidity']=float(inTempdata[1]) #I know, this is in Humidity, but I'm going to treat it as outside
            f.close
        except:
            log.error("Can't read Extratemp2 and/or inHumidity")
            log.error(inTempdata)
        try:
            #get the  air quality values from the AQ sensor
            f=open('/var/tmp/aqi')
            value= f.read() #this will be in the format x,y where x is the PM2.5 and y is the PM10
            AQdata = eval(value) #split into a tuple
            data['pm2_5']=float(AQdata[0]) 
            data['pm10_0']=float(AQdata[1])
            f.close
        except:
            log.error("Can't read AQ data")

        try:
            #get the office inside temp and baro pressure from ESP32 device
            f=open('/var/tmp/barometer')
            value= f.read() #this will be in the format x,y where x is the temp in degF and y is the pressure in kPa
            pdata = value[1:-2].split(",")
            data['inTemp']=(float(pdata[0])-32)*5/9 #convert to degC
            data['pressure']=float(pdata[1]) 
            print("pressure ",data['pressure'])
            f.close
        except:
            log.error("Can't read pressure or office temp")
            log.error(pdata)


        try:
                           #get the pool temperature values from pool temp sensor
            f=open('/var/tmp/pooltemp')
            value= f.read() #this will be in the format x,y where x is the temp in degF and y is nothing
            pooltemp = eval(value) #split into a tuple
            pooltempC = (float(pooltemp[0]) - 32) * 5/9 # convert to C
            data['soilTemp1']=pooltempC
            f.close
        except:
            log.error("Can't read pool temp data")
        data['channel'] = None
        data['sensor_id'] = None
        data['rssi'] = None
        data['sensor_battery'] = None
        return data

    @staticmethod
    def check_R1(raw):
        ok = True
        if raw[1] & 0x0f == 0x0f and raw[3] == 0xff:
            log.info("R1: no sensors found: %s" % _fmt_bytes(raw))
            ok = False
        else:
            if raw[3] & 0x0f != 1 and raw[3] & 0x0f != 8:
                log.info("R1: bogus message flavor (%02x): %s" % (raw[3], _fmt_bytes(raw)))
                ok = False
            if raw[9] != 0xff and raw[9] != 0x00:
                log.info("R1: bogus final byte (%02x): %s" % (raw[9], _fmt_bytes(raw)))
                ok = False
            if raw[8] & 0x0f < 0 or raw[8] & 0x0f > 3:
                log.info("R1: bogus signal strength (%02x): %s" % (raw[8], _fmt_bytes(raw)))
                ok = False
        return ok

    @staticmethod
    def decode_R2(raw, use_constants=True, ignore_bounds=False):
        data = dict()
        return data

    @staticmethod
    def decode_R3(raw):
        data = dict()
        return data

    @staticmethod
    def decode_channel(data):
        return Station.CHANNELS.get(data[1] & 0xf0)

    @staticmethod
    def decode_sensor_id(data):
        return ((data[1] & 0x0f) << 8) | data[2]

    @staticmethod
    def decode_rssi(data):
        # signal strength goes from 0 to 3, inclusive
        # according to nincehelser, this is a measure of the number of failed
        # sensor queries, not the actual RF signal strength
        return data[8] & 0x0f

    @staticmethod
    def decode_sensor_battery(data):
        # 0x7 indicates battery ok, 0xb indicates low battery?
        a = (data[3] & 0xf0) >> 4
        return 0 if a == 0x7 else 1

    @staticmethod
    def decode_windspeed(data):
        # extract the wind speed from an R1 message
        # return value is kph
        # for details see http://www.wxforum.net/index.php?topic=27244.0
        # minimum measurable speed is 1.83 kph
        n = ((data[4] & 0x1f) << 3) | ((data[5] & 0x70) >> 4)
        if n == 0:
            return 0.0
        return 0.8278 * n + 1.0

    @staticmethod
    def decode_winddir(data):
        # extract the wind direction from an R1 message
        # decoded value is one of 16 points, convert to degrees
        v = data[5] & 0x0f
        return Station.IDX_TO_DEG.get(v)

    @staticmethod
    def decode_outtemp(data):
        # extract the temperature from an R1 message
        # return value is degree C
        a = (data[5] & 0x0f) << 7
        b = (data[6] & 0x7f)
        return (a | b) / 18.0 - 40.0

    @staticmethod
    def decode_outhumid(data):
        # extract the humidity from an R1 message
        # decoded value is percentage
        return data[7] & 0x7f

    @staticmethod
    def decode_rain(data):
        # decoded value is a count of bucket tips
        # each tip is 0.01 inch, return value is cm
        return (((data[6] & 0x3f) << 7) | (data[7] & 0x7f)) * 0.0254

    @staticmethod
    def decode_pt(data, use_constants=True, ignore_bounds=False):
        # decode pressure and temperature from the R2 message
        # decoded pressure is mbar, decoded temperature is degree C
        c1,c2,c3,c4,c5,c6,c7,a,b,c,d = Station.get_pt_constants(data)

        if not use_constants:
            # use a linear approximation for pressure and temperature
            d2 = ((data[21] & 0x0f) << 8) + data[22]
            if d2 >= 0x0800:
                d2 -= 0x1000
            d1 = (data[23] << 8) + data[24]
            return Station.decode_pt_acurite(d1, d2)
        elif (c1 == 0x8000 and c2 == c3 == 0x0 and c4 == 0x0400
              and c5 == 0x1000 and c6 == 0x0 and c7 == 0x0960
              and a == b == c == d == 0x1):
            # this is a MS5607 sensor, typical in 02032 consoles
            d2 = ((data[21] & 0x0f) << 8) + data[22]
            if d2 >= 0x0800:
                d2 -= 0x1000
            d1 = (data[23] << 8) + data[24]
            return Station.decode_pt_MS5607(d1, d2)
        elif (0x100 <= c1 <= 0xffff and
              0x0 <= c2 <= 0x1fff and
              0x0 <= c3 <= 0x400 and
              0x0 <= c4 <= 0x1000 and
              0x1000 <= c5 <= 0xffff and
              0x0 <= c6 <= 0x4000 and
              0x960 <= c7 <= 0xa28 and
              (0x01 <= a <= 0x3f and 0x01 <= b <= 0x3f and
               0x01 <= c <= 0x0f and 0x01 <= d <= 0x0f) or ignore_bounds):
            # this is a HP038 sensor.  some consoles return values outside the
            # specified limits, but their data still seem to be ok.  if the
            # ignore_bounds flag is set, then permit values for A, B, C, or D
            # that are out of bounds, but enforce constraints on the other
            # constants C1-C7.
            d2 = (data[21] << 8) + data[22]
            d1 = (data[23] << 8) + data[24]
            return Station.decode_pt_HP03S(c1,c2,c3,c4,c5,c6,c7,a,b,c,d,d1,d2)
        log.error("R2: unknown calibration constants: %s" % _fmt_bytes(data))
        return None, None

    @staticmethod
    def decode_pt_HP03S(c1,c2,c3,c4,c5,c6,c7,a,b,c,d,d1,d2):
        # for devices with the HP03S pressure sensor
        if d2 >= c5:
            dut = d2 - c5 - ((d2-c5)/128) * ((d2-c5)/128) * a / (2<<(c-1))
        else:
            dut = d2 - c5 - ((d2-c5)/128) * ((d2-c5)/128) * b / (2<<(c-1))
        off = 4 * (c2 + (c4 - 1024) * dut / 16384)
        sens = c1 + c3 * dut / 1024
        x = sens * (d1 - 7168) / 16384 - off
        p = 0.1 * (x * 10 / 32 + c7)
        t = 0.1 * (250 + dut * c6 / 65536 - dut / (2<<(d-1)))
        return p, t

    @staticmethod
    def decode_pt_MS5607(d1, d2):
        # for devices with the MS5607 sensor, do a linear scaling
        return Station.decode_pt_acurite(d1, d2)

    @staticmethod
    def decode_pt_acurite(d1, d2):
        # apparently the new (2015) acurite software uses this function, which
        # is quite close to andrew daviel's reverse engineered function of:
        #    p = 0.062585727 * d1 - 209.6211
        #    t = 25.0 + 0.05 * d2
        p = d1 / 16.0 - 208
        t = 25.0 + 0.05 * d2
        return p, t

    @staticmethod
    def decode_inhumid(data):
        # FIXME: decode inside humidity
        return None

    @staticmethod
    def get_pt_constants(data):
        c1 = (data[3] << 8) + data[4]
        c2 = (data[5] << 8) + data[6]
        c3 = (data[7] << 8) + data[8]
        c4 = (data[9] << 8) + data[10]
        c5 = (data[11] << 8) + data[12]
        c6 = (data[13] << 8) + data[14]
        c7 = (data[15] << 8) + data[16]
        a = data[17]
        b = data[18]
        c = data[19]
        d = data[20]
        return (c1,c2,c3,c4,c5,c6,c7,a,b,c,d)

class AcuRiteConfEditor(weewx.drivers.AbstractConfEditor):
    @property
    def default_stanza(self):
        return """
[AcuRite]
    # This section is for AcuRite weather stations.
    # The station model, e.g., 'AcuRite 01025' or 'AcuRite 02032C'
    model = 'AcuRite 01035'
    # The driver to use:
    driver = weewx.drivers.acurite
"""


# define a main entry point for basic testing of the station without weewx
# engine and service overhead.  invoke this as follows from the weewx root dir:
#
# PYTHONPATH=bin python bin/weewx/drivers/acurite.py

if __name__ == '__main__':
    import optparse

    import weewx
    import weeutil.logger

    weewx.debug = 1

    weeutil.logger.setup('acurite', {})

    usage = """%prog [options] [--help]"""

    parser = optparse.OptionParser(usage=usage)
    parser.add_option('--version', dest='version', action='store_true',
                      help='display driver version')
    (options, args) = parser.parse_args()

    if options.version:
        print("acurite driver version %s" % DRIVER_VERSION)
        exit(0)

    test_r1 = True
    test_r2 = True
    test_r3 = False
    delay = 12*60
    with Station() as s:
        while True:
            ts = int(time.time())
            tstr = "%s (%d)" % (time.strftime("%Y-%m-%d %H:%M:%S %Z",
                                              time.localtime(ts)), ts)
            if test_r1:
                r1 = s.read_R1()
                print(tstr, _fmt_bytes(r1), Station.decode_R1(r1))
                delay = min(delay, 18)
            if test_r2:
                r2 = s.read_R2()
                print(tstr, _fmt_bytes(r2), Station.decode_R2(r2))
                delay = min(delay, 60)
            if test_r3:
                try:
                    x = s.read_x()
                    print(tstr, _fmt_bytes(x))
                    for i in range(17):
                        r3 = s.read_R3()
                        print(tstr, _fmt_bytes(r3))
                except usb.USBError as e:
                    print(tstr, e)
                delay = min(delay, 12*60)
            time.sleep(delay)
