#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
import json
import pickle
import math
import numpy as np
import matplotlib.pyplot as plt

from mpl_toolkits.mplot3d import Axes3D
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from numpy import linalg as LA
from scipy.optimize import curve_fit

from .udp import UDP
from .influx import Influx
from .helper import Helper
from .routines import Routines

from grafana_annotation_server.cli import Annotation

buffer = []

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
def scratch_3():

    fig = plt.figure()
    ax = fig.add_subplot(221)
    ay = fig.add_subplot(222)
    az = fig.add_subplot(223)
    bx = fig.add_subplot(224)
    # by = fig.add_subplot(335)
    # bz = fig.add_subplot(336)
    # cx = fig.add_subplot(337)
    # cy = fig.add_subplot(338)
    # cz = fig.add_subplot(339)

    idb = Influx()

    click.echo("😐  Loading the data from influxdb.")

    lim = 400
    offset = 0

    static = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'static_9_sep_1534')))
    walk   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'walk_9_sep_1511')))
    run   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'run_9_sep_1505')))

    static_ftr = list(Routines.sep_15_2332(*static))
    walk_ftr = list(Routines.sep_15_2332(*walk))
    run_ftr = list(Routines.sep_15_2332(*run))

    ax.plot([_[3] for _ in static_ftr])
    ax.plot([_[3] for _ in walk_ftr])
    ax.plot([_[3] for _ in run_ftr])

    ay.plot([_[0] for _ in static_ftr])
    ay.plot([_[0] for _ in walk_ftr])
    ay.plot([_[0] for _ in run_ftr])

    az.plot([_[1] for _ in static_ftr])
    az.plot([_[1] for _ in walk_ftr])
    az.plot([_[1] for _ in run_ftr])

    bx.plot([_[2] for _ in static_ftr])
    bx.plot([_[2] for _ in walk_ftr])
    bx.plot([_[2] for _ in run_ftr])

    ax.set_ylim([0, 30])
    ay.set_ylim([0, 5])
    az.set_ylim([0, 5])
    plt.show()


@main.command()
@click.argument('annotation_db', type=str)
def scratch(annotation_db):

    annotations = Annotation(annotation_db)

    idb = Influx()

    fig = plt.figure()
    ax = fig.add_subplot(221)
    ay = fig.add_subplot(222)
    az = fig.add_subplot(223)

    f = lambda x, a, b, c, d, q, w, e: (a * np.sin(b * x + c) + d + q * np.arctan(w * x + e))
    f = lambda x, d, q, w, e: d + q * np.arctan(w * x + e)

    for i in idb.probe_annotation('accelerometer', annotations.get('transition_2509')):
        x, y, z = zip(*i)
        ax.plot(x)
        # ax.plot(y)
        # ax.plot(z)

    plt.show()
