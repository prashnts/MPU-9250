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



    # ax.plot(static[0])
    # ay.plot(static[1])
    # az.plot(static[2])

    # bx.plot(walk[0])
    # by.plot(walk[1])
    # bz.plot(walk[2])

    # cx.plot(run[0])
    # cy.plot(run[1])
    # cz.plot(run[2])

    ax.set_ylim([0, 30])
    ay.set_ylim([0, 5])
    az.set_ylim([0, 5])
    # bx.set_ylim([-5, 5])
    # by.set_ylim([-5, 5])
    # bz.set_ylim([-5, 5])
    # cx.set_ylim([-5, 5])
    # cy.set_ylim([-5, 5])
    # cz.set_ylim([-5, 5])
    plt.show()


@main.command()
@click.argument('annotation_db', type=str)
def scratch(annotation_db):

    annotations = Annotation(annotation_db)
    print(annotations.get('transition_2509'))

    # fig = plt.figure()
    # ax = fig.add_subplot(111, projection='3d')

    # idb = Influx()

    # click.echo("😐  Loading the data from influxdb.")
    # lim = 50
    # offset = 0

    # static = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'static_9_sep_1534')))
    # walk   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'walk_9_sep_1511')))
    # run   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'run_9_sep_1505')))

    # static_ftr = list(Routines.sep_15_2332(*static))
    # walk_ftr = list(Routines.sep_15_2332(*walk))
    # run_ftr = list(Routines.sep_15_2332(*run))

    # click.echo("😣  Flattening features.")

    # svm_static_val = list(static_ftr)
    # svm_walk_val   = list(walk_ftr)
    # svm_run_val    = list(run_ftr)

    # lim = min(len(svm_static_val), len(svm_walk_val), len(svm_run_val))

    # click.echo("😐  Plotting features.")

    # for i in svm_static_val[:lim]:
    #     ax.scatter(*i[1:3], c = 'b', marker = 'p')

    # for i in svm_walk_val[:lim]:
    #     ax.scatter(*i[1:3], c = 'r', marker = '*')

    # for i in svm_run_val[:lim]:
    #     ax.scatter(*i[1:3], c = 'g', marker = 'o')

    # ax.set_xlim([0, 10])
    # ax.set_ylim([0, 10])
    # #ax.set_zlim([0, 10])
    # ax.set_xlabel('X Label')
    # ax.set_ylabel('Y Label')
    # ax.set_zlabel('Z Label')

    # plt.show()
