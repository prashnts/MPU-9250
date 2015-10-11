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
import pandas as pd
import itertools

from mpl_toolkits.mplot3d import Axes3D
from sklearn.svm import SVC
from sklearn.decomposition import PCA
from numpy import linalg as LA
from scipy.optimize import curve_fit
from itertools import chain
from pandas.tools.plotting import lag_plot, autocorrelation_plot
from pandas.tools.plotting import parallel_coordinates, andrews_curves, scatter_matrix, radviz

from .udp import UDP
from .influx import Influx
from .helper import Helper
from .helper import Stupidity
from .routines import Routines
from .sample_dump import ChainProbes, LabelDict

from grafana_annotation_server.cli import Annotation

buffer = []

@click.group()
@click.pass_context
def main(ctx):
    """
    """
    pass

@main.command()
def scratch_f():
    plt.figure()
    plt.ylim([-10, 100])
    # plt.xkcd()
    ftr = []

    for i in LabelDict:
        w = ChainProbes(i)
        fv_pr = []
        c = 0
        print(i)
        for row in w:
            c += 1
            if c < 1000:
                continue
            elif c > 2200:
                break
            f = Routines.feature_vector(zip(*row)) + [i]
            #print(f)
            ftr.append(f)

    hdr = ["w_e", "tssq", "gradient", "gradient_binned", "moving_mean", "Name"]

    df = pd.DataFrame(ftr, columns = hdr)
    radviz(df, 'Name')
    # parallel_coordinates(df, class_column = "Name")
    plt.show()

@main.command()
@click.option('--kernel', '-k', type=str, help='SVC Kernel')
@click.option('--degree', '-d', type=int, help='SVC Degree (Only for Polynomial)')
@click.argument('pickle_svm_object', type=click.File('wb'))
def train(pickle_svm_object, kernel = 'poly', degree = 2):

    click.echo("😐  Creating features.")

    s = Samples()
    plt.figure()
    X = []
    Y = []

    for i in s.LABEL_DICT_USED:
        w = s.probe(i)
        fv_pr = []
        c = 0
        for row in w:
            c += 1
            print(c)
            # if c == 100:
            #     break
            X.append(Routines.feature_vector(zip(*row)))
            Y.append(int(s.LABEL_DICT_USED[i]))

    click.echo("😐  Done Creating features.")
    click.echo("😏  Training SVM.")

    support_vector_classifier = SVC(kernel = 'rbf')
    support_vector_classifier.fit(X, Y)

    click.echo("😄  Dumping SVM Object.")

    pickle.dump(support_vector_classifier, pickle_svm_object)


@main.command()
@click.argument('pickle_svm_object', type=click.File('rb'))
def test(pickle_svm_object):
    click.echo("😐  Creating features.")
    sv = pickle.load(pickle_svm_object)

    s = Samples()

    for i in s.LABEL_DICT_USED:
        w = s.probe(i)
        c = 0
        for row in w:
            c += 1
            cls = sv.predict(Routines.feature_vector(zip(*row)))
            print("Predicted: {0}; Actual: {1}".format(cls, i))

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
@click.argument('pickled_svm_object', type=click.File('rb'))
def f_test(pickled_svm_object, port):
    support_vector_classifier = pickle.load(pickled_svm_object)

    @UDP.handler
    def svm_test(**kwargs):
        global buffer
        if 'dat' in kwargs:
            click.echo(".", nl=False)
            buffer.append(kwargs['dat']['accelerometer'])

        if len(buffer) == 64:
            buf_ftr = Routines.feature_vector(zip(*buffer))
            pred = support_vector_classifier.predict(buf_ftr)
            #print(buf_ftr)
            buffer[:] = []

            if pred in [4, 5, 6]:
                click.echo("😆  {0} Stationary".format(pred))
            if pred == 1:
                click.echo("😆  {0} Walking".format(pred))
            if pred == 2:
                click.echo("😆  {0} Walking Up".format(pred))
            if pred == 3:
                click.echo("🚶  {0} Walking Down".format(pred))

    UDP.start_routine('', port)

if __name__ == "__main__":
    main()
