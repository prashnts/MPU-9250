#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import json
import signal
import socketserver
import pickle
from itertools import cycle
from influxdb import InfluxDBClient
from sklearn.svm import SVC

progress_pool = cycle(["_  ", "__ ", "___"])
client = None
support_vector_classifier = None
data_class_global  = None
sample_rate_global = None

def CSV_parse_to_dict(handle, column_delim = ","):
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

def write_to_influx(dat):
    """
    Logs `dat` to the InfluxDB database.
    Args:
        dat (dict): Data dictionary. The missing fields are auto set to float(0)
    """
    json_body = [
        {
            "measurement": "accelerometer",
            "tags": {
                "mmt_class": data_class_global,
                "sample_rate": sample_rate_global
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
                "mmt_class": data_class_global,
                "sample_rate": sample_rate_global
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
                "mmt_class": data_class_global,
                "sample_rate": sample_rate_global
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
                "mmt_class": data_class_global,
                "sample_rate": sample_rate_global
            },
            "fields": {
                "roll"  : dat['Roll']  if 'Roll'  in dat else 0.0,
                "pitch" : dat['Pitch'] if 'Pitch' in dat else 0.0,
                "yaw"   : dat['Yaw']   if 'Yaw'   in dat else 0.0
            }
        }
    ]
    client.write_points(json_body)

def gather_class():
    """
    Updates the global data class and sample rate methods.
    """
    global data_class_global, sample_rate_global
    data_class_global = click.prompt('Please enter the data class', type=str)
    sample_rate_global = click.prompt('Please enter the sampling rate of the device', type=str)

    if click.confirm('Proceed?'):
        return
    else:
        gather_class()

class UDP_Retrieve(socketserver.DatagramRequestHandler):
    """
    Retrieves and Logs the UDP Datagram packets (not encoded) through local Broadcast to the InfluxDB instance.
    Extends the socketserver class.
    """

    #: str: Default Column Header pattern of the Datagram
    column_headers_default = "Timestamp,Accel_X,Accel_Y,Accel_Z,Roll,Pitch,Yaw,Quat.X,Quat.Y,Quat.Z,Quat.W,RM11,RM12,RM13,RM21,RM22,RM23,RM31,RM32,RM33,GravAcc_X,GravAcc_Y,GravAcc_Z,UserAcc_X,UserAcc_Y,UserAcc_Z,RotRate_X,RotRate_Y,RotRate_Z,MagHeading,TrueHeading,HeadingAccuracy,MagX,MagY,MagZ,Lat,Long,LocAccuracy,Course,Speed,Altitude"

    def handle(self):
        """
        This method is called on every UDP packets that are recieved.
        """
        try:
            data = self.get_dict(self.rfile.readline().rstrip().decode())
            write_to_influx(data)
            inf = click.style("[LOGGING UDP DATA] {0}".format(next(progress_pool)), fg = 'cyan')
            click.secho('\r{0}'.format(inf), nl = False)
        except ValueError:
            pass

    def get_dict(self, data):
        """
        Creates a Dictionary of the incoming UDP data string.
        """
        column_data = data.split(",")
        column_headers = self.column_headers_default.split(",")

        if len(column_data) == len(column_headers):
            dat_map = {column_headers[_]: float(column_data[_]) for _ in range(0, len(column_headers))}
            return dat_map

        return dict()

class UDP_Test(UDP_Retrieve):
    """

    """

    buffered_dat = []
    direction    = 0

    def handle(self):
        """
        This method is called on every UDP packets that are recieved.
        """
        try:
            data = self.get_dict(self.rfile.readline().rstrip().decode())
            self.buffered_dat.append(self.transform_dat(data))

            if len(self.buffered_dat) == 6:
                point = Helper.combine(self.buffered_dat)
                self.direction = support_vector_classifier.predict(point)
                self.buffered_dat[:] = []
                click.echo("Direction:{0}".format(Helper.translate_direction(self.direction)))

            # inf = click.style("[Direction:{0}] {1}".format(Helper.translate_direction(self.direction), next(progress_pool)), fg = 'cyan')
            # click.secho('\r{0}'.format(inf), nl = False)
        except ValueError:
            print(":(")
            pass
        pass

    def buffer(self):
        """

        """
        pass

    def transform_dat(self, dat):
        """
        """
        return {
            "x": dat['MagX'] if 'MagX' in dat else 0.0,
            "y": dat['MagY'] if 'MagY' in dat else 0.0,
            "z": dat['MagZ'] if 'MagZ' in dat else 0.0
        }

class Helper(object):
    def mean(dat):
        return sum(dat) / len(dat)

    def combine(dat):
        out = []

        for ax in ['x', 'y', 'z']:
            out.append(Helper.mean([_[ax] for _ in dat]))

        return out

    def generate_features(dat):
        """
        """
        overlapped_chunks = list(zip(*[dat[_:] for _ in range(6)]))[0::2]

        return [Helper.combine(_) for _ in overlapped_chunks]

    def translate_direction(id):
        """
        """
        return [
            "Unknw",
            "North",
            "South",
            " East",
            " West"
        ][id]

@click.group()
@click.pass_context
def main(ctx):
    """
    """
    print("Beginning Data Logging")

@main.command()
@click.argument('input_file', type=click.File('r'))
def csv_to_influx(input_file):
    """Logs CSV data into Influx DB."""
    global client

    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')

    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Parsing the CSV.")

    data = CSV_parse_to_dict(input_file)

    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Logging the data.")

    for dat in data:
        write_to_influx(dat)

        inf = click.style("[LOGGING DATA] {0}".format(next(progress_pool)), fg = 'cyan')
        click.secho('\r{0}'.format(inf), nl = False)

    click.echo("")
    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Done logging data.")

@main.command()
@click.option('--port_number', '-p', type=int, required=True, help='UDP Cast Port Number')
def udp(port_number):
    """
    Begins the UDP
    """
    global client
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')
    udp_client = socketserver.UDPServer(('',port_number), UDP_Retrieve)
    gather_class()
    click.echo("Waiting for data.")
    udp_client.serve_forever()

@main.command()
@click.option('--kernel', '-k', type=str, help='SVC Kernel')
@click.option('--degree', '-d', type=int, help='SVC Degree (Only for Polynomial)')
@click.argument('pickle_svm_object', type=click.File('wb'))
def svm(pickle_svm_object, kernel = 'poly', degree = 2):
    """
    Trains a SVM object with the Direction data samples.
    Feature Vector: 6Hz chunk of a 30Hz sample:
        [mean(magnetometer_x), mean(magnetometer_y), mean(magnetometer_z)]
    Vector Sampling: The chunks are chosen such that they may overlap a few times.
        This will increase redundancy, but will make sure that a random sample length of size 6 is easily accounted for.
    Class Labels: The definition is:
        1 -> North, 2 -> South, 3 -> East, and 4 -> West
    """
    global client, support_vector_classifier
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')

    # Retrieve data from the InfluxDB
    result_north = list(client.query("SELECT x, y, z FROM magnetometer WHERE mmt_class='north_test_one';"))[0]
    result_south = list(client.query("SELECT x, y, z FROM magnetometer WHERE mmt_class='south_test_one';"))[0]
    result_east = list(client.query("SELECT x, y, z FROM magnetometer WHERE mmt_class='east_test_one';"))[0]
    result_west = list(client.query("SELECT x, y, z FROM magnetometer WHERE mmt_class='west_test_two';"))[0]

    X = []
    Y = []

    lower_bound = 20
    upper_bound = min([len(result_north), len(result_south), len(result_east), len(result_west)])

    print(upper_bound)

    X += Helper.generate_features(result_north[lower_bound:upper_bound])
    size = len(X)
    Y += [1] * size

    X += Helper.generate_features(result_south[lower_bound:upper_bound])
    Y += [2] * size

    X += Helper.generate_features(result_east[lower_bound:upper_bound])
    Y += [3] * size

    X += Helper.generate_features(result_west[lower_bound:upper_bound])
    Y += [4] * size

    support_vector_classifier = SVC(kernel='poly', degree=2)
    support_vector_classifier.fit(X, Y)

    pickle.dump(support_vector_classifier, pickle_svm_object)


@main.command()
@click.option('--port_number', '-p', type=int, required=True, help='UDP Cast Port Number')
@click.argument('pickled_svm_object', type=click.File('rb'))
def udp_test(pickled_svm_object, port_number):
    global support_vector_classifier

    support_vector_classifier = pickle.load(pickled_svm_object)

    udp_client = socketserver.UDPServer(('',port_number), UDP_Test)
    click.echo("Waiting for data.")
    udp_client.serve_forever()

if __name__ == "__main__":
    main()