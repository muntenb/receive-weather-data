#!/bin/python3

from configparser import ConfigParser
import subprocess as subp
from os import path, remove
from datetime import datetime, timezone
from influxdb import InfluxDBClient
import time

class homeClimate:
    """Class to process the climate data"""
    def __init__(self, configFile='homeClimate.conf'):
        config = ConfigParser()
        print('Reading configuration from {}'.format(configFile))
        config.read(configFile)
        # sensor data
        self.frequency      = config['Default']['frequency']
        self.gain           = config['Default']['gain']
        self.threshold      = config['Default']['threshold']
        self.timeout        = config['Default']['timeout']
        self.max_counter    = int(config['Default']['max_counter'])
        self.debug          = bool(int(config['Default']['debug_flag']))
        self.bathroom_id    = config['Default']['bathroom_id']
        self.livingroom_id  = config['Default']['livingroom_id']
        self.bedroom_id     = config['Default']['bedroom_id']
        self.childsroom_id  = config['Default']['childsroom_id']
        self.larder_id      = config['Default']['larder_id']
        #self.outside_id     = config['Default']['outside_id']
        self.homeoffice_id  = config['Default']['homeoffice_id']
        self.id_idx         = int(config['Default']['id_idx'])
        self.datafile       = config['Default']['datafile'] 
        # database values
        self.update_interval = int(config['Influxdb']['update_interval'])
        self.db_host = config['Influxdb']['host']
        self.db_port = config['Influxdb']['port']
        self.db_user = config['Influxdb']['user']
        self.db_pw   = config['Influxdb']['password']
        self.db      = config['Influxdb']['database']
        # values not read from config file
        self.data_complete = False
        self.sensors = {self.bathroom_id : 'Badezimmer',
                        self.livingroom_id : 'Wohnzimmer',
                        self.bedroom_id : 'Schlafzimmer',
                        self.childsroom_id : 'Kinderzimmer',
                        self.larder_id : 'Speisekammer',
                        self.homeoffice_id : 'Arbeitszimmer'}
                        #self.outside_id : 'Terrasse',
        self.data = {}

    def remove_test_file(self):
        if path.isfile(self.datafile):
            remove(self.datafile)

    def read_sensors_data(self, timeout=None):
        self.data_complete = False
        if timeout == None:
            timeout = self.timeout
        print("Receiving data ...", end=" ")
        tfrec = subp.Popen(['tfrec',
                            '-g {}'.format(self.gain),
                            '-f {}'.format(self.frequency),
                            '-w {}'.format(timeout),
                            '-t {}'.format(self.threshold)],
                            stdout=subp.PIPE,
                            stderr=subp.DEVNULL,
                            universal_newlines=True)
        try:
            outs, err = tfrec.communicate(timeout=2*float(self.timeout))
        except subp.TimeoutExpired:
            tfrec.kill()
            outs, err = tfrec.communicate()
        if self.debug == True:
            print(outs)
        print("... finished.")
        return outs

    def convert_sensors_data(self, input_data):
        for line in input_data.splitlines():
            values = line.split(sep=' ')
            id = values[self.id_idx]
            if self.debug == True:
                print("id = {}".format(id))
            if id in list(self.sensors): 
                temp = float(values[self.id_idx+1].replace("+", ""))
                hum  = float(values[self.id_idx+2].replace("%", ""))
                self.data[self.sensors[id]] = [temp, hum]  
        if self.debug == True:        
            print(self.data)

    def print_sensors_data(self):
        print("Captured sensors: {}".format(len(list(self.data))))
        for room in sorted(list(self.data)):
            values = self.data[room]
            print("{:15} Temp: {:5} Hum: {:2}%".format(room, values[0], values[1]))

    def check_if_data_complete(self):
        rooms = list(self.sensors.values())
        captured_rooms = []
        for room, values in self.data.items():
            if room in rooms and values:
                rooms.remove(room)
                captured_rooms.append(room)
        if len(rooms) == 0 and len(list(self.data)) == len(list(self.sensors)):
            print("Data complete at {}".format(self.get_current_local_time()))
            self.data_complete = True
        print("Got {}/{} rooms: {}".format( len(captured_rooms),
                                            len(list(self.sensors)),
                                            captured_rooms))
        return self.data_complete

    def get_current_utc_time(self):
        self.utcdatetime = datetime.now(timezone.utc)
        return self.utcdatetime

    def get_current_local_time(self):
        self.localdatetime = datetime.now()
        return self.localdatetime

    def write_data_to_database(self):
        print("Sending data to database {}".format(self.db))
        if self.data_complete == False:
            print("Sending incomplete data set at {}".format(self.get_current_local_time())) 
        try:
            utctime = self.get_current_utc_time()
            client = InfluxDBClient(self.db_host, self.db_port, self.db_user,
                                    self.db_pw, self.db)
            for room, values in self.data.items():
                json_body = [
                        { 
                            "measurement": "climate",
                            "tags": {
                                "room": room 
                            },
                            "time": utctime.isoformat(),
                            "fields": { 
                                "temperature": values[0],
                                "humidity": values[1] 
                            }
                         }
                ]    
                if self.debug == True:
                    print(json_body)
                client.write_points(json_body)
        except Exception as Ex:
            print(Ex)
            print("Could not write data to database at {}".format(self.get_current_local_time()))
    
    def clear_data(self):
        self.data = {}
        self.data_complete = False

    def write_and_display_sensors_data(self):
        tfrec = subp.Popen(['tfrec', 
                            '-g {}'.format(self.gain), 
                            '-f {}'.format(self.frequency),
                            '-e echo $(date +%Y%m%d-%H%M%S) >> {}'.format(self.datafile)],
                            stdout=subp.PIPE, 
                            universal_newlines=True)
        try:
            outs, err = tfrec.communicate(timeout=30)
        except subp.TimeoutExpired: 
            tfrec.kill()
            outs, err = tfrec.communicate()
            #print(outs)
        with open(self.datafile, 'r') as fid:
            for line in fid.readlines():
                data = line.split()
                print('{}  {:15} Temp: {:5} rh: {:2}%'.format(
                        data[0], self.sensors[data[1]], data[2], data[3]))

if __name__ == "__main__":
    hC = homeClimate()
    while True:
        counter = 0
        start_time = datetime.now()
        while not hC.data_complete:  
            print("({:2}/{}) ".format(counter+1, hC.max_counter), end="")
            data = hC.read_sensors_data()
            hC.convert_sensors_data(data)
            hC.check_if_data_complete()
            if hC.debug == True:
                hC.print_sensors_data()
            counter = counter + 1
            if counter >= hC.max_counter:
                break
        hC.print_sensors_data()
        hC.write_data_to_database()
        # clear the data
        hC.clear_data()
        end_time = datetime.now()
        diff_time = end_time - start_time
        sleeptime = hC.update_interval  - int(diff_time.total_seconds())
        print("Sleeping for {}".format(sleeptime))
        time.sleep(sleeptime)

