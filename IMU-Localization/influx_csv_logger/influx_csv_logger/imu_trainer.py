#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
import socketserver
import json
import pickle

from sklearn.svm import SVC
from scipy.optimize import curve_fit
from itertools import cycle
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
        xyz = ['x', 'y', 'z']
        ypr = ['yaw', 'pitch', 'roll']

        json_body = [
            {
                "measurement": "accelerometer",
                "tags": {
                    "mmt_class": data_class
                },
                "fields": {
                    _: __ for (_, __) in zip(xyz, dat['accelerometer'])
                }
            },
            {
                "measurement": "gyroscope",
                "tags": {
                    "mmt_class": data_class
                },
                "fields": {
                    _: __ for (_, __) in zip(xyz, dat['gyroscope'])
                }
            },
            {
                "measurement": "magnetometer",
                "tags": {
                    "mmt_class": data_class
                },
                "fields": {
                    _: __ for (_, __) in zip(xyz, dat['magnetometer'])
                }
            },
            {
                "measurement": "ahrs",
                "tags": {
                    "mmt_class": data_class
                },
                "fields": {
                    _: __ for (_, __) in zip(ypr, dat['ahrs'])
                }
            }
        ]

        self.client.write_points(json_body)

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

class UDP(socketserver.DatagramRequestHandler):
    """
    Retrieves and Logs the UDP Datagram packets through local Broadcast to the InfluxDB instance.
    Extends the socketserver class.
    """

    # There's no prettier way.
    #: (str) Pattern of the 
    COL_HEAD = "Timestamp,Accel_X,Accel_Y,Accel_Z,Roll,Pitch,Yaw,Quat.X,Quat.Y,Quat.Z,Quat.W,RM11,RM12,RM13,RM21,RM22,RM23,RM31,RM32,RM33,GravAcc_X,GravAcc_Y,GravAcc_Z,UserAcc_X,UserAcc_Y,UserAcc_Z,RotRate_X,RotRate_Y,RotRate_Z,MagHeading,TrueHeading,HeadingAccuracy,MagX,MagY,MagZ,Lat,Long,LocAccuracy,Course,Speed,Altitude".split(",")

    def _transform_dict(self, data):
        """
        Creates a Dictionary of the incoming UDP data string.
        """
        column_data = data.split(",")

        if len(column_data) == len(self.COL_HEAD):
            return {self.COL_HEAD[_]: float(column_data[_]) for _ in range(0, len(self.COL_HEAD))}

        return dict()

    def probe(self):
        """
        Translates the dict to standard probe data.
        """

        data = self._transform_dict(self.rfile.readline().rstrip().decode())

        acce = ['Accel_X', 'Accel_Y', 'Accel_Z']
        gyro = ['RotRate_X', 'RotRate_Y', 'RotRate_Z']
        magn = ['MagX', 'MagY', 'MagZ']
        ahrs = ['Roll', 'Pitch', 'Yaw']

        return {
            'accelerometer': [data[_] for _ in acce],
            'gyroscope':     [data[_] for _ in gyro],
            'magnetometer':  [data[_] for _ in magn],
            'ahrs':          [data[_] for _ in ahrs]
        }

    def handle(self):
        """
        This method is called on every UDP packets that are recieved.
        On every received data, the callable, `self.data_handler` is called with the data.
        """
        try:
            if not UDP.handler:
                raise
            else:
                UDP.handler(dat = self.probe())
        except ValueError:
            pass

    @staticmethod
    def handler(func):
        """
        Decorator function, registers data handler.
        """
        UDP.handler = func

    @staticmethod
    def start_routine(hostname, port):
        """
        Helper function that starts the routine.
        """
        c = socketserver.UDPServer((hostname, port), UDP)
        c.serve_forever()

class Helper(object):
    """
    """

    #: (cycle) A circular queue to show progress.
    pool = cycle(["😀  ", "😃  ", "😄  "])

    @staticmethod
    def gather_class():
        """
        Gathers the Motion Class from User.
        """
        data_class_global = click.prompt('Motion Class Tag', type = str)

        if click.confirm('Proceed?'):
            return data_class_global
        else:
            gather_class()

    @staticmethod
    def concatenate(measurements):
        """
        Concatenates the measurements taken here.
        Example: concatenate(zip([[x1], [x2] ...], [[y1], [y2], ...]))
                 returns [[x1, y1], [x2, y2], ...]
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

    @staticmethod
    def feature(transform_function, measurements):
        """
        Features are calculated out of a series of values.
        """
        pass

class Routines(object):
    """
    Collations of multiple training Routines.
    """

    class WalkingStationary(object):
        def feature(data):
            pass

        def train(data):
            pass

@click.group()
@click.pass_context
def main(ctx):
    """
    """
    pass

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
def log_udp(port):
    """
    Logs the raw sensor data incoming through UDP in the InfluxDB.
    """
    mmt_class = Helper.gather_class()

    influx_client = Influx()

    @UDP.handler
    def put_in(**kwargs):
        if 'dat' in kwargs:
            influx_client.write(kwargs['dat'], mmt_class)
            click.secho('\rLogging: {0}'.format(next(Helper.pool)), nl = False)

    UDP.start_routine('', port)

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
@click.argument('pickled', type = click.File('r'))
def test(pickled, port):
    """
    """

    classifier = pickle.load(pickled)

    dat = []

    @UDP.handler
    def svm_test(**kwargs):
        global dat

        pass

    UDP.start_routine('', port)

@main.command()
def debug():
    """
    Debug commands.
    """

    print(locals())

if __name__ == "__main__":
    main()
