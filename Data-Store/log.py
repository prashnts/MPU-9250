#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import click
import platform
import glob
import json
import signal
import sys
from itertools import cycle
from influxdb import InfluxDBClient

serial_port = serial.Serial()
client = None
progress_pool = cycle(["X  ", "__ ", "___"])

@click.command()
@click.option('--baud_rate', default = 19200, help='Override the default baud_rate value.')
@click.option('--verbose', default = False, help='Prints the retrieved json on console.')
def routine(verbose, baud_rate):
    """
    This script intends to log the data output from an Arduino connected to the PC
    and running the MPU-9250 firmware provided.
    The data is logged to an InfluxDB instance as soon as it arrives.

    All tuning/synchronization is untested and there may be race around conditions
    here.
    """

    open_serial_port(baud_rate)
    click.secho("[INF] ", fg = 'cyan', nl = False)
    click.secho("Serial Port '{0}' opened.".format(serial_port.name))
    while True:
        try:
            line = serial_port.readline().decode('utf-8')
            act_upon(line)
        except Exception:
            click.secho("\n[ERR] ", fg = 'cyan', nl = False, err = True)
            click.secho("Connection Lost.", err = True, fg = 'red')
            click.secho("[INF] ", fg = 'cyan', nl = False)
            click.secho("Terminating Process.")
            sys.exit(1)

def open_serial_port(baud_rate):
    """
    Prompts to select the correct Serial Port and then uses that to gather the
    data from.
    """
    global serial_port

    ports = list_serial_ports()

    for index, port in enumerate(ports, start = 1):
        click.secho("[{0}]".format(index), fg = 'cyan', nl = False)
        click.secho(" {0}".format(port),   fg = 'yellow')

    port_number = click.prompt('Please enter the Serial Port Number', type = int)
    try:
        ser = serial.Serial(ports[port_number - 1], baud_rate)
        serial_port = ser
    except IndexError:
        click.secho("[ERR] ", fg = 'cyan', nl = False, err = True)
        click.secho("Incorrect port number. Terminating.", err = True, fg = 'red')
        sys.exit(1)
    except Exception:
        click.secho("[ERR] ", fg = 'cyan', nl = False, err = True)
        click.secho("Cannot open the Serial Port at '{0}'.".format(ports[port_number - 1]), err = True, fg = 'red')
        click.secho("[INF] ", fg = 'cyan', nl = False)
        click.secho("Terminating Process.".format(index))
        sys.exit(1)

def act_upon(line):
    """
    Acts upon the lines received from the Device.
    """

    try:
        dat = json.loads(line)
        if all([
            'accl' in dat,
            'gyro' in dat,
            'cmps' in dat,
            'ypr' in dat,
            'qtr' in dat
        ]):
            inf = click.style("[LOGGING DATA] {0}".format(next(progress_pool)), fg = 'cyan')
            click.secho('\r{0}'.format(inf), nl = False)
            # Add data in influx now
            json_body = [
                {
                    "measurement": "accelerometer",
                    "tags": {
                        "host": "server01",
                    },
                    "fields": {
                        "x": dat['accl'][0],
                        "y": dat['accl'][1],
                        "z": dat['accl'][2]
                    }
                },
                {
                    "measurement": "gyroscope",
                    "tags": {
                        "host": "server01",
                    },
                    "fields": {
                        "x": dat['gyro'][0],
                        "y": dat['gyro'][1],
                        "z": dat['gyro'][2]
                    }
                },
                {
                    "measurement": "magnetometer",
                    "tags": {
                        "host": "server01",
                    },
                    "fields": {
                        "x": dat['cmps'][0],
                        "y": dat['cmps'][1],
                        "z": dat['cmps'][2]
                    }
                },
                {
                    "measurement": "principle_axes",
                    "tags": {
                        "host": "server01",
                    },
                    "fields": {
                        "yaw":   dat['ypr'][0],
                        "pitch": dat['ypr'][1],
                        "roll":  dat['ypr'][2]
                    }
                },
                {
                    "measurement": "quaternion",
                    "tags": {
                        "host": "server01",
                    },
                    "fields": {
                        "x": dat['qtr'][0],
                        "y": dat['qtr'][1],
                        "z": dat['qtr'][2]
                    }
                }
            ]
            client.write_points(json_body)

    except ValueError:
        if "online" in line:
            click.secho("[INF] ", fg = 'cyan', nl = False)
            click.secho("Sensors are Online. Beginning Data Logging.")
            click.secho("[INF] ", fg = 'yellow', nl = False)
            click.secho("Press CTRL + C to stop.", )

def signal_handler(signal, frame):
    """
    Handles SIGINT.
    """

    click.secho("\n[INF] ", fg = 'cyan', nl = False)
    click.secho("Closing Ports and Exiting.")
    serial_port.close()
    sys.exit(0)

def list_serial_ports():
    """
    Scans and lists the available Serial Ports.
    """

    system_name = platform.system()
    if system_name == "Windows":
        # Scan for available ports.
        available = []
        for i in range(256):
            try:
                s = serial.Serial(i)
                available.append(i)
                s.close()
            except serial.SerialException:
                pass
        return available
    elif system_name == "Darwin":
        # Mac
        return glob.glob('/dev/tty.*') #+ glob.glob('/dev/cu.*')
    else:
        # Assume Linux or something else
        return glob.glob('/dev/ttyS*') + glob.glob('/dev/ttyUSB*')

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    client = InfluxDBClient('localhost', 8086, 'root', 'root', 'example')
    #client.create_database('example')
    routine()
