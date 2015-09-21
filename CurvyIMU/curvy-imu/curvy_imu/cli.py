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
@click.argument('csv', type = click.File('r'))
def log_csv(csv):
    """
    Logs the CSV formatted sensor data in the InfluxDB.
    """
    mmt_class = Helper.gather_class()

    influx_client = Influx()

    def _transform(data):
        """
        Internal method for CSV transformation.
        """

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

    rows = Helper.load_csv(csv)

    for row in rows:
        influx_client.write(_transform(row), mmt_class)
        click.secho('\rLogging: {0}'.format(next(Helper.pool)), nl = False)

@main.command()
# @click.argument('csv1', type = click.File('r'))
# @click.argument('csv2', type = click.File('r'))
def scratch():

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    idb = Influx()

    click.echo("😐  Loading the data from influxdb.")

    static = idb.probe('accelerometer', limit = 32, offset = 100, tag = 'static_9_sep_1534')
    walk   = idb.probe('accelerometer', limit = 32, offset = 100, tag = 'walk_9_sep_1511')
    run    = idb.probe('accelerometer', tag = 'running_stationary')

    click.echo("😐  Creating features.")

    ftr_static = Routines.sep_15_2332(*zip(*static))
    ftr_walk   = Routines.sep_15_2332(*zip(*walk))
    ftr_run    = Routines.sep_15_2332(*zip(*run))

    click.echo("😣  Flattening features.")

    svm_static_val = list(ftr_static)
    svm_walk_val   = list(ftr_walk)
    svm_run_val    = list(ftr_run)

    lim = min(len(svm_static_val), len(svm_walk_val))#, len(svm_run_val))

    click.echo("😐  Plotting features.")

    for i in svm_static_val[:lim]:
        ax.scatter(*i, c = 'b', marker = 'p')

    for i in svm_walk_val[:lim]:
        ax.scatter(*i, c = 'r', marker = '*')

    for i in svm_run_val[:lim]:
        ax.scatter(*i, c = 'g', marker = 'o')

    ax.set_xlim([0, 10])
    ax.set_ylim([0, 10])
    #ax.set_zlim([0, 10])
    ax.set_xlabel('X Label')
    ax.set_ylabel('Y Label')
    ax.set_zlabel('Z Label')

    plt.show()

@main.command()
def scratch_2():

    fig = plt.figure()
    ax = fig.add_subplot(331)
    ay = fig.add_subplot(332)
    az = fig.add_subplot(333)
    bx = fig.add_subplot(334)
    by = fig.add_subplot(335)
    bz = fig.add_subplot(336)
    cx = fig.add_subplot(337)
    cy = fig.add_subplot(338)
    cz = fig.add_subplot(339)

    idb = Influx()

    click.echo("😐  Loading the data from influxdb.")

    lim = 30
    offset = 440

    static = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'static_9_sep_1534')))
    walk   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'walk_9_sep_1511')))
    run   = list(zip(*idb.probe('accelerometer', limit = lim, offset = offset, tag = 'run_9_sep_1505')))

    def f(x, a, b, c, d):
        return a * np.sin(b * x + c) + d
    def f2(x, a, b, c, d):
        return a * np.sin((2 * np.pi * b * x) + c) + d

    def fit_plt(l):
        # Fit the data.
        popt = Helper.curve_fit(f, l)
        #print([popt, np.var(l)])
        #popt = Helper.curve_fit(f2, l)
        #print(popt)
        # create set of vals.
        return [f(_, *popt) for _ in range(len(l))]

    def band_pass(l):
        avg = sum(l) / len(l)

        def _filter(x):
            if x >= avg:
                return 1
            return 0

        return [_filter(_) for _ in l]

    def ban_pass(l):
        popt = Helper.curve_fit(f, l)
        # create set of vals.
        v = sum([abs(_) for _ in l])/len(l)
        return [v * f(_, *popt) for _ in range(len(l))]

    def avg(l):
        avg = sum(l) / len(l)
        return [avg] * len(l)

    ax.plot(static[0])
    ax.plot(fit_plt(static[0]))
    ay.plot(static[1])
    ay.plot(fit_plt(static[1]))
    az.plot(static[2])
    az.plot(fit_plt(static[2]))

    print(Helper.discreet_wave_energy(static[0] + static[1] + static[2]))
    print(Helper.discreet_wave_energy(walk[0] + walk[1] + walk[2]))
    print(Helper.discreet_wave_energy(run[0] + run[1] + run[2]))

    bx.plot(walk[0])
    bx.plot(fit_plt(walk[0]))
    by.plot(walk[1])
    by.plot(fit_plt(walk[1]))
    bz.plot(walk[2])
    bz.plot(fit_plt(walk[2]))
    bz.plot(Helper.autocorrelation(walk[2]))

    cx.plot(run[0])
    cx.plot(fit_plt(run[0]))
    #cx.plot([abs(_) for _ in run[0]])
    #cx.plot(band_pass(run[0]))
    cx.plot(ban_pass(run[0]))
    cy.plot(run[1])
    cy.plot(fit_plt(run[1]))
    cy.plot(Helper.autocorrelation(run[1]))
    #cy.plot(fit_plt(Helper.autocorrelation(run[1])))
    cz.plot(run[2])
    cz.plot(Helper.autocorrelation(run[2]))
    cz.plot(fit_plt(run[2]))

    ax.set_ylim([-5, 5])
    ay.set_ylim([-5, 5])
    az.set_ylim([-5, 5])
    bx.set_ylim([-5, 5])
    by.set_ylim([-5, 5])
    bz.set_ylim([-5, 5])
    cx.set_ylim([-5, 5])
    cy.set_ylim([-5, 5])
    cz.set_ylim([-5, 5])
    plt.show()

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

    lim = 640
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
@click.argument('annotations_json', type=str)
def scratch_4(annotations_json):
    pass

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

    static = idb.probe('accelerometer', tag = 'static_9_sep_1534')
    walk   = idb.probe('accelerometer', tag = 'walk_9_sep_1511')

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

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
@click.argument('pickled_svm_object', type=click.File('rb'))
def sep_9_1242_test(pickled_svm_object, port):
    support_vector_classifier = pickle.load(pickled_svm_object)

    @UDP.handler
    def svm_test(**kwargs):
        global buffer
        if 'dat' in kwargs:
            buffer.append(kwargs['dat']['accelerometer'])

        if len(buffer) == 16:
            buf_ftr = Routines.sep_9_1242_feature(zip(*buffer))
            pred = support_vector_classifier.predict(buf_ftr)

            buffer[:] = []

            if pred == 1:
                click.echo("😆  {0} Stationary".format(pred))

            if pred == 2:
                click.echo("🚶  {0} Walk".format(pred))


    UDP.start_routine('', port)


@main.command()
@click.option('--kernel', '-k', type=str, help='SVC Kernel')
@click.option('--degree', '-d', type=int, help='SVC Degree (Only for Polynomial)')
@click.argument('pickle_svm_object', type=click.File('wb'))
def sep17_1(pickle_svm_object, kernel = 'poly', degree = 2):
    """
    Training routine written on September 17, 2015 at 13:41.
    Gets data tagged as `static_9_sep_1534`, `run_9_sep_1505`, and `walk_9_sep_1511` from influxdb.
    Creates features through Routine Method sep_15_2332.
    """

    idb = Influx()

    click.echo("😐  Loading the data from influxdb.")

    static = idb.probe('accelerometer', tag = 'static_9_sep_1534')
    walk   = idb.probe('accelerometer', tag = 'walk_9_sep_1511')
    run    = idb.probe('accelerometer', tag = 'run_9_sep_1505')

    click.echo("😐  Creating features.")

    ftr_static = Routines.sep_15_2332(*zip(*static))
    ftr_walk   = Routines.sep_15_2332(*zip(*walk))
    ftr_run    = Routines.sep_15_2332(*zip(*run))

    click.echo("😣  Flattening features.")

    svm_static_val = list(ftr_static)
    svm_walk_val   = list(ftr_walk)
    svm_run_val    = list(ftr_run)

    lim = min(len(svm_static_val), len(svm_walk_val), len(svm_run_val))

    click.echo("😐  Concatinating features.")

    X  = svm_static_val[:lim]
    Y  = [1] * lim
    X += svm_walk_val[:lim]
    Y += [2] * lim
    X += svm_run_val[:lim]
    Y += [3] * lim

    click.echo("😏  Training SVM.")

    support_vector_classifier = SVC(kernel = kernel, degree = degree)
    support_vector_classifier.fit(X, Y)

    click.echo("😄  Dumping SVM Object.")

    pickle.dump(support_vector_classifier, pickle_svm_object)

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
@click.argument('pickled_svm_object', type=click.File('rb'))
def sep17_1_test(pickled_svm_object, port):
    support_vector_classifier = pickle.load(pickled_svm_object)

    @UDP.handler
    def svm_test(**kwargs):
        global buffer
        if 'dat' in kwargs:
            click.echo(".", nl=False)
            buffer.append(kwargs['dat']['accelerometer'])

        if len(buffer) == 16:
            buf_ftr = Routines.sep_15_2332_feature(zip(*buffer))
            pred = support_vector_classifier.predict(buf_ftr)

            buffer[:] = []

            if pred == 1:
                click.echo("😆  {0} Stationary".format(pred))

            if pred == 2:
                click.echo("🚶  {0} Walk".format(pred))

            if pred == 3:
                click.echo("🏃  {0} Run".format(pred))

    UDP.start_routine('', port)

if __name__ == "__main__":
    main()
