#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import click
import json
from itertools import cycle
from influxdb import InfluxDBClient

progress_pool = cycle(["_  ", "__ ", "___"])
client = None

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

    #: List[Dict]: Output data.
    out_list = []

    for row in handle:
        column_data = row.rstrip().split(",")
        if len(column_data) == len(column_headers):
            dat_map = {column_headers[i]: float(column_data[i]) for i in range(0, len(column_headers))}
            out_list.append(dat_map)

    return out_list

def put_in(dat, data_class, sample_rate):
    json_body = [
        {
            "measurement": "accelerometer",
            "tags": {
                "mmt_class": data_class,
                "sample_rate": sample_rate
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
                "sample_rate": sample_rate
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
                "sample_rate": sample_rate
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
                "sample_rate": sample_rate
            },
            "fields": {
                "roll"  : dat['Roll']  if 'Roll'  in dat else 0.0,
                "pitch" : dat['Pitch'] if 'Pitch' in dat else 0.0,
                "yaw"   : dat['Yaw']   if 'Yaw'   in dat else 0.0
            }
        }
    ]
    client.write_points(json_body)
    pass

@click.command()
@click.option('--data_class',  '-c', type=str, help='Data Class')
@click.option('--sample_rate', '-s', type=str, help='Sampling Rate of the Sensor')
@click.argument('input_file', type=click.File('r'))
def csv_to_influx(input_file, sample_rate, data_class):
    """Logs CSV data into Influx DB."""
    global client
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')

    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Parsing the CSV.")

    data = CSV_parse_to_dict(input_file)

    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Logging the data.")

    for dat in data:
        put_in(dat, data_class, sample_rate)

        inf = click.style("[LOGGING DATA] {0}".format(next(progress_pool)), fg = 'cyan')
        click.secho('\r{0}'.format(inf), nl = False)

    click.echo("")
    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Done logging data.")

if __name__ == "__main__":
    csv_to_influx()
