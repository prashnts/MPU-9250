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
from pandas.tools.plotting import parallel_coordinates, andrews_curves

from .udp import UDP
from .influx import Influx
from .helper import Helper
from .helper import Stupidity
from .routines import Routines
from .sample_dump import Samples

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
    s = Samples()
    plt.figure()
    ftr = []

    for i in s.LABEL_DICT:
        w = s.probe(i)
        fv_pr = []
        c = 0
        for row in w:
            c += 1
            if c == 1000:
                break
            ftr.append(Routines.feature_vector(zip(*row)) + [i])

    hdr = ["w_e", "gradient", "gradient_binned", "keypoint", "moving_mean_v", "ax_var", "sm_keypoint", "sm_gradient", "sm_gradient_binned", "Name"]

    df = pd.DataFrame(ftr, columns = hdr)
    parallel_coordinates(df, "Name")
    plt.show()
    andrews_curves(df, "Name")
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

    for i in s.LABEL_DICT:
        w = s.probe(i)
        fv_pr = []
        c = 0
        for row in w:
            c += 1
            print(c)
            # if c == 100:
            #     break
            X.append(Routines.feature_vector(zip(*row)))
            Y.append(int(s.LABEL_DICT[i]))

    click.echo("😐  Done Creating features.")
    click.echo("😏  Training SVM.")

    support_vector_classifier = SVC(kernel = 'rbf', C=1e-2, gamma=1e1)
    support_vector_classifier.fit(X, Y)

    for i in s.LABEL_DICT:
        print(i)
        w = s.probe(i)
        c = 0
        for row in w:
            c += 1

            if c == 10:
                break
            cls = support_vector_classifier.predict(Routines.feature_vector(zip(*row)))
            print("Predicted: {0}; Actual: {1}".format(cls, i))

    click.echo("😄  Dumping SVM Object.")

    pickle.dump(support_vector_classifier, pickle_svm_object)


@main.command()
@click.argument('pickle_svm_object', type=click.File('rb'))
def test(pickle_svm_object):
    click.echo("😐  Creating features.")
    print(pickle.load(pickle_svm_object))

    s = Samples()

    for i in s.LABEL_DICT:
        w = s.probe(i)
        c = 0
        for row in w:
            c += 1
            if c < 990:
                continue
            if c == 1000:
                break
            cls = sv.predict(Routines.feature_vector(zip(*row)))
            print("Predicted: {0}; Actual: {1}".format(cls, i))
