#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import click
import time

from influxdb import InfluxDBClient
from itertools import chain
from .helper import Helper

class Influx(object):
    """
    Proxy for Influx DB.
    """

    def __init__(self):
        """
        """
        self.client = InfluxDBClient('localhost', 8086, 'root', 'root', 'imu_data')
        self._init_client()

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

        args = {_: arguments[_] if _ in arguments else None for _ in ['tag', 'time_lower', 'time_upper', 'limit', 'offset']}

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

        if args['limit'] and args['offset']:
            q += " limit {0} offset {1};".format(args['limit'], args['offset'])
        elif args['limit']:
            q += " limit {0};".format(args['limit'])
        else:
            q += ";"

        return self.client.query(q)

    def _init_client(self):
        json_body = [{
            "measurement": "meta",
            "fields": {
                "type": "Login"
            }
        }]
        try:
            self.client.write_points(json_body)
        except Exception:
            self.client.create_database('imu_data')
            self.client.write_points(json_body)
            click.echo("Created a New Database `imu_data`.")

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

    def import_json(self, file_handle, relative_time = True):
        """
        """
        try:
            dat = json.loads(file_handle.read())

            for result in dat['results']:
                for series in result['series']:
                    col = series['columns']
                    tags = series['tags']
                    name = series['name']

                    for i in series['values']:
                        json_body = [{
                            "measurement": name,
                            "tags": tags,
                            "time": i[0],
                            "fields": {
                                _: float(__) for (_, __) in zip(col[1:], i[1:])
                            }
                        }]
                        self.client.write_points(json_body)
                        click.echo('\rImporting: {0}'.format(next(Helper.pool)), nl = False)
            return True

        except json.decoder.JSONDecodeError:
            click.echo("Invalid JSON.")

        except Exception as e:
            click.echo("ERR:" + str(e))

        return False

    def probe_annotation(self, name, annotation_dict, wouldchain = False, *args, **kwargs):
        """
        Returns annotation data dicts.
        """

        time_format = lambda x: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(float(x) / 1000))
        gen = []

        for time_range in annotation_dict:
            kwargs['time_lower'] = time_format(time_range[0])
            kwargs['time_upper'] = time_format(time_range[1])

            if wouldchain is True:
                gen.append(self.probe(name, **kwargs))
            else:
                yield self.probe(name, **kwargs)

        return gen
