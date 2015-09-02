#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""

"""

import json
from influxdb import InfluxDBClient

class Influx(object):
    """
    Proxy for Influx DB.
    """

    def __init__(self):
        """
        """
        self.client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')

    def _flatten(self, dat):
        """
        *Flattens* the data to a list.
        Example:
            {x: _x, y: _y, z: _z} = [_x, _y, _z]
            {yaw: _x, pitch: _y, roll: _z} = [_x, _y, _z]
            {*unknown*}: [arbitrary order]
        Args:
            dat (generator): The result returned by the influxdb object.
        """
        for row in dat:
            if 'x' in row:
                """
                We have a <x, y, z> vector.
                """
                yield [row['x'], row['y'], row['z']]
            elif 'yaw' in row:
                """
                We have a <yaw, pitch, roll> vector.
                """
                yield [row['yaw'], row['pitch'], row['roll']]

    def _measurement(self, measurement, arguments):
        """
        Returns the Measurement for a specific tag.
        Args:
            measurement (str): The measurement.
            arguments (dict): Dictionary of the Arguments passed on to the function.
        Returns:
            ResultSet: The InfluxDB result instance.
        """

        args = {_: arguments[_] if _ in arguments else None for _ in ['tag', 'time_lower', 'time_upper', 'limit']}

        q = "SELECT * FROM {0}".format(measurement)

        if any([args['tag'], args['time_lower'], args['time_upper']]):
            q += " WHERE "

        if args['tag']:
            q += "mmt_class='{0}'".format(args['tag'])

        if args['tag'] and any([args['time_upper'], args['time_lower']]):
            q += " AND "

        if args['time_lower']:
            q += "time > '{0}'".format(args['time_lower'])

        if args['time_lower'] and args['time_upper']:
            q += " AND "

        if args['time_upper']:
            q += "time < '{0}'".format(args['time_upper'])

        if args['time_upper'] and args['limit']:
            q += " AND "

        if args['limit']:
            q += " limit {0};".format(args['limit'])
        else:
            q += ";"

        return self.client.query(q)

    def write(self, dat, data_class):
        """
        Logs `dat` to the InfluxDB database.
        Args:
            dat (dict): Data dictionary. The missing fields are auto set to float(0)
        """
        json_body = [
            {
                "measurement": "accelerometer",
                "tags": {
                    "mmt_class": data_class,
                },
                "fields": {
                    "x": dat['Accel_X'] if 'Accel_X' in dat else 0.0,
                    "y": dat['Accel_Y'] if 'Accel_Y' in dat else 0.0,
                    "z": dat['Accel_Z'] if 'Accel_Z' in dat else 0.0
                }
            },
            {
                "measurement": "gyroscope",
                "tags": {
                    "mmt_class": data_class,
                },
                "fields": {
                    "x": dat['RotRate_X'] if 'RotRate_X' in dat else 0.0,
                    "y": dat['RotRate_Y'] if 'RotRate_Y' in dat else 0.0,
                    "z": dat['RotRate_Z'] if 'RotRate_Z' in dat else 0.0
                }
            },
            {
                "measurement": "magnetometer",
                "tags": {
                    "mmt_class": data_class,
                },
                "fields": {
                    "x": dat['MagX'] if 'MagX' in dat else 0.0,
                    "y": dat['MagY'] if 'MagY' in dat else 0.0,
                    "z": dat['MagZ'] if 'MagZ' in dat else 0.0
                }
            },
            {
                "measurement": "ahrs",
                "tags": {
                    "mmt_class": data_class,
                },
                "fields": {
                    "roll"  : dat['Roll']  if 'Roll'  in dat else 0.0,
                    "pitch" : dat['Pitch'] if 'Pitch' in dat else 0.0,
                    "yaw"   : dat['Yaw']   if 'Yaw'   in dat else 0.0
                }
            }
        ]
        client.write_points(json_body)

    def probe(self, name, *args, **kwargs):
        """
        Returns the measurements taken on a particular "probe".
        Args:
            name (str): The name of the Probe.
            tag (str): The mmt_class tag attached to the measurement.
            time_lower (str): InfluxDB format lower limit of time.
            time_upper (str): InfluxDB format upper limit of time.
            limit (int): Limits the number of rows returned.
        Returns:
            generator: Generator of the probe columns.
        """
        out = self._measurement(name, kwargs).get_points()
        return self._flatten(out)

    def concatenate(self, measurements):
        """
        Concatenates the measurements taken here.
        Args:
            measurements (zip): A zip concatenation of the measurements.
        Returns:
            generator: Generator instance containing the place wise concatenation of the measurements.
        """
        for i in measurements:
            result = []
            for j in i:
                for k in j:
                    result.append(k)
            yield result

    def feature(self, transform_function, measurements):
        """
        """
        pass

class UDPGet(socketserver.DatagramRequestHandler):
    """
    Retrieves and Logs the UDP Datagram packets through local Broadcast to the InfluxDB instance.
    Extends the socketserver class.
    """

    #: str: Default Column Header pattern of the Datagram
    column_headers_default = "Timestamp,Accel_X,Accel_Y,Accel_Z,Roll,Pitch,Yaw,Quat.X,Quat.Y,Quat.Z,Quat.W,RM11,RM12,RM13,RM21,RM22,RM23,RM31,RM32,RM33,GravAcc_X,GravAcc_Y,GravAcc_Z,UserAcc_X,UserAcc_Y,UserAcc_Z,RotRate_X,RotRate_Y,RotRate_Z,MagHeading,TrueHeading,HeadingAccuracy,MagX,MagY,MagZ,Lat,Long,LocAccuracy,Course,Speed,Altitude"

    def __init__(self, data_handler):
        """
        """
        self.data_handler = data_handler

    def handle(self):
        """
        This method is called on every UDP packets that are recieved.
        On every received data, the callable, `self.data_handler` is called with the data.
        """
        try:
            data = self._transform_dict(self.rfile.readline().rstrip().decode())
            self.data_handler(data)
        except ValueError:
            self.value_error_count += 1

    def _transform_dict(self, data):
        """
        Creates a Dictionary of the incoming UDP data string.
        """
        column_data = data.split(",")
        column_headers = self.column_headers_default.split(",")

        if len(column_data) == len(column_headers):
            dat_map = {column_headers[_]: float(column_data[_]) for _ in range(0, len(column_headers))}
            return dat_map
        return dict()

a = Influx()
b = a.probe("accelerometer", tag = "walking_stationary", time_lower = '2015-08-31T08:01:01.21659282Z', time_upper = '2015-08-31T08:02:48.22270603Z')
c = a.probe("gyroscope", tag = "walking_stationary", time_lower = '2015-08-31T08:01:01.21659282Z', time_upper = '2015-08-31T08:02:48.22270603Z')
e = a.probe("magnetometer", tag = "walking_stationary", time_lower = '2015-08-31T08:01:01.21659282Z', time_upper = '2015-08-31T08:02:48.22270603Z')

print(list(a.concatenate(zip(b, c, e)))[0])