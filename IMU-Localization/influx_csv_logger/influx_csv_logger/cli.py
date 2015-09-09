#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
import socketserver
import json
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D
from sklearn.svm import SVC
from scipy.optimize import curve_fit
from numpy import linalg as LA
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
    def curve_fit(transform_function, measurements):
        """
        Features are calculated out of a series of values.
        """
        x_values = np.array(range(0, len(measurements)))
        popt, pcov = curve_fit(transform_function, x_values, measurements)

        return list(popt)

    @staticmethod
    def load_csv(handle, column_delim = ","):
        """
        Initializes the class. The Dictionary structure is built through the first line of the CSV data file. Line delimiter is not customizable and is "\n" by default.
        Args:
            handle (File): File handler. The handle should be opened as "r", or "rw".
            column_delim (str): Column Delimiter Symbol. Default: ",".
        Returns:
            list: A List of Dict each corresponding to the rows.
        Raises:
            ValueError: If non-float data exists in the rows.
        """

        # Reach the beginning of the file
        handle.seek(0)

        # Get the CSV columns - Remove trailing chomp, and split at ","
        column_headers = handle.readline().rstrip().split(",")

        for row in handle:
            column_data = row.rstrip().split(",")
            if len(column_data) == len(column_headers):
                dat_map = {column_headers[i]: float(column_data[i]) for i in range(0, len(column_headers))}
                yield dat_map

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

    feature, svm_object = pickle.load(pickled)

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

class Routines(object):
    """
    Wrapper for custom routine functions.
    Just coz Swag.
    """

    @staticmethod
    def sep_9_1242(x, y, z):
        """
        This method creates a feature in Four stages:
        1. Create overlapping chunks of the x, y, z axis data, 16 length.
        2. Fit individual axes on `y = aSin(bx + c) + d`.
        3. Create a 3x4 matrix, with each row having: [a, b, c, d].
        4. Remove column with parameter `d` (vertical shift) to get a 3x3 matrix.
        5. Yield the eigenvalue of the matrix - feature.

        Args:
            x (list): x axis probe data.
            y (list): y axis probe data.
            z (list): z axis probe data.

        Returns:
            (generator): 3D Feature Vector
        """

        #: Overlapped x, y, and z axis data.
        #  Data length -> 16
        x_o = zip(*[x[_:] for _ in range(16)])
        y_o = zip(*[y[_:] for _ in range(16)])
        z_o = zip(*[z[_:] for _ in range(16)])

        #: Gathers row wise data.
        row = zip(x_o, y_o, z_o)

        for val_set in row:
            yield Routines.sep_9_1242_feature(val_set)

    @staticmethod
    def sep_9_1242_feature(val_set):
        """
        Supplementary method for method `sep_9_1242`.
        It performs the subtask 2 to 5 for the previous method.
        It has been separated from parent method for modular usage while training the streaming data.

        Args:
            val_set (list): List containing the list of chunks of data.

        Returns:
            (list): Eigenvalues, feature.
        """

        def func(x, a, b, c, d):
            #: The fit-function
            #: y = aSin(bx + c) + d
            return a * np.sin(b * x + c) + d

        ftr = []
        for col in val_set:
            #: Curve fit each column to get the period, phase shift, vertical
            #: shift, and amplitude.
            try:
                #: if we find optimal fit, then append.
                popt = Helper.curve_fit(func, col)
                ftr.append(popt)
            except RuntimeError:
                #: Let it be (TM)
                #: To keep the structure of the `ftr` intact
                #  we do this stupid hack.
                ftr.append([0, 0, 0, 0])

        #: Yield a single feature, combining all of the above
        ftr_cmb = zip(*ftr)

        ampl  = next(ftr_cmb)   # Amplitude
        phase = next(ftr_cmb)   # Phase
        ph_sh = next(ftr_cmb)   # Phase Shift
        ve_sh = next(ftr_cmb)   # Vertical Shift

        eig_val, eig_vec = LA.eig([ampl, phase, ph_sh])

        return [np.absolute(_) for _ in eig_val]

@main.command()
@click.argument('csv1', type = click.File('r'))
@click.argument('csv2', type = click.File('r'))
def scratch(csv1, csv2):

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    row = list(Helper.load_csv(csv1))
    x = [_['x'] for _ in row]
    y = [_['y'] for _ in row]
    z = [_['z'] for _ in row]

    for i in Routines.sep_9_1242(x, y, z):
        ax.scatter(*i, c = 'r', marker = 'o')

    row = list(Helper.load_csv(csv2))
    x = [_['x'] for _ in row]
    y = [_['y'] for _ in row]
    z = [_['z'] for _ in row]

    for i in Routines.sep_9_1242(x, y, z):
        ax.scatter(*i, c = 'b', marker = '^')

    ax.set_xlim(left = -10, right = 10)
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.show()

@main.command()
@click.option('--kernel', '-k', type=str, help='SVC Kernel')
@click.option('--degree', '-d', type=int, help='SVC Degree (Only for Polynomial)')
@click.argument('pickle_svm_object', type=click.File('wb'))
def sep_9_1242(pickle_svm_object, kernel = 'poly', degree = 2):
    """
    Training routine written on September 9, 2015 at 12:42.
    Gets data tagged as `stationary_stationary` and `walking_stationary` from influxdb.
    Creates features through Routine Method sep_9_1242.
    """

    idb = Influx()

    click.echo("😐  Loading the data from influxdb.")

    static = idb.probe('accelerometer', tag = 'stationary_stationary')
    walk   = idb.probe('accelerometer', tag = 'walking_stationary')

    click.echo("😐  Creating features.")

    ftr_static = Routines.sep_9_1242(*zip(*static))
    ftr_walk   = Routines.sep_9_1242(*zip(*walk))

    click.echo("😣  Flattening features.")

    svm_static_val = list(ftr_static)
    svm_walk_val   = list(ftr_walk)

    lim = min(len(svm_static_val), len(svm_walk_val))

    click.echo("😐  Concatinating features.")

    X = svm_static_val[:lim]
    Y = [1] * lim
    X += svm_walk_val[:lim]
    Y += [2] * lim

    click.echo("😏  Training SVM.")

    support_vector_classifier = SVC(kernel = kernel, degree = degree)
    support_vector_classifier.fit(X, Y)

    click.echo("😄  Dumping SVM Object.")

    pickle.dump(support_vector_classifier, pickle_svm_object)

if __name__ == "__main__":
    main()
