#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import json
import signal
import socketserver
from itertools import cycle
from influxdb import InfluxDBClient

progress_pool = cycle(["_  ", "__ ", "___"])
client = None
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
    column_headers_default = "Timestamp,Accel_X,Accel_Y,Accel_Z,Roll,Pitch,Yaw,Quat.X,Quat.Y,Quat.Z,Quat.W,RM11,RM12,RM13,RM21,RM22,RM23,RM31,RM32,RM33,GravAcc_X,GravAcc_Y,GravAcc_Z,UserAcc_X,UserAcc_Y,UserAcc_Z,RotRate_X,RotRate_Y,RotRate_Z,MagHeading,TrueHeading,HeadingAccuracy,MagX,MagY,MagZ,Lat,Long,LocAccuracy,Course,Speed,Altitude"

    def handle(self):
        try:
            data = self.get_dict(self.rfile.readline().rstrip().decode())
            write_to_influx(data)
            inf = click.style("[LOGGING UDP DATA] {0}".format(next(progress_pool)), fg = 'cyan')
            click.secho('\r{0}'.format(inf), nl = False)
        except ValueError:
            pass

    def get_dict(self, data):
        column_data = data.split(",")
        column_headers = self.column_headers_default.split(",")

        if len(column_data) == len(column_headers):
            dat_map = {column_headers[i]: float(column_data[i]) for i in range(0, len(column_headers))}
            return dat_map

        return dict()

# @click.group()
# @click.argument('input_file', type=click.File('r'))
# def csv_to_influx(input_file):
#     """Logs CSV data into Influx DB."""
#     global client

#     client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')

#     click.secho("[INF] ", fg = 'cyan', nl = False)
#     click.secho("Parsing the CSV.")

#     data = CSV_parse_to_dict(input_file)

#     click.secho("[INF] ", fg = 'cyan', nl = False)
#     click.secho("Logging the data.")

#     for dat in data:
#         write_to_influx(dat)

#         inf = click.style("[LOGGING DATA] {0}".format(next(progress_pool)), fg = 'cyan')
#         click.secho('\r{0}'.format(inf), nl = False)

#     click.echo("")
#     click.secho("[INF] ", fg = 'cyan', nl = False)
#     click.secho("Done logging data.")

@click.group()
@click.pass_context
def main(ctx):
    print("Beginning Data Loggine")

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

if __name__ == "__main__":
    main()
