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
import pydot

from mpl_toolkits.mplot3d import Axes3D
from sklearn.svm import SVC
from sklearn import tree
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.externals.six import StringIO
from sklearn.decomposition import PCA
from sklearn.cross_validation import train_test_split
from numpy import linalg as LA
from scipy.optimize import curve_fit
from itertools import chain
from pandas.tools.plotting import lag_plot, autocorrelation_plot
from pandas.tools.plotting import parallel_coordinates, andrews_curves, scatter_matrix, radviz

from .udp import UDP
from .influx import Influx
from .helper import Helper
from .helper import Stupidity
from .helper import Tools
from .routines import Routines
from .sample_dump import ChainProbes, LabelDict, Labels, LabelDictC, LabelsC, LabelDictD, LabelsD, LabelDictE, LabelsE

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
    # plt.style.use(['bmh','ggplot'])
    # plt.xkcd()
    ftr = []

    lab = ["WALKING", "RUNNING", "JOGGING", "SITTING", "BIKING", "WALKING_UPSTAIRS"]
    for i in lab:
        w = ChainProbes(i)
        fv_pr = []
        c = 0
        print(i)
        for row in w:
            c += 1
            if c == 1000:
                break
            f = Routines.feature_vector(zip(*row)) + [i]
            #print(f)
            ftr.append(f)

    hdr = ["w_e", "tssq", "gradient", "gradient_binned", "moving_mean", "Name"]

    df = pd.DataFrame(ftr, columns = hdr)

    # plt..yscale('log')

    radviz(df, class_column = "Name", alpha=0.01)
    plt.show()
    # andrews_curves(df, 'Name')
    # plt.show()

@main.command()
@click.argument('dmp', type=click.File('wb'))
def train_tree(dmp):

    click.echo("😐  Creating features.")

    X = []
    Y = []

    lab_use, lab_use_dict = LabelsE, LabelDictE

    cnts = []

    for i in lab_use_dict:
        w = ChainProbes(i)
        fv_pr = []
        c = 0
        for row in w:
            c += 1
            if c == 2000:
                break
            X.append(Routines.feature_vector(zip(*row)))
            Y.append(int(lab_use_dict[i]))
        cnts.append([i, c, lab_use_dict[i]])
        print([i, c, lab_use_dict[i]])

    print(cnts)

    click.echo("😐  Done Creating features.")
    click.echo("😏  Training.")

    X_train, X_test, y_train, y_test = train_test_split(X, Y, random_state=0)

    dtc = DecisionTreeClassifier().fit(X_train, y_train)
    rfc = RandomForestClassifier(n_estimators=20).fit(X_train, y_train)
    srb = SVC(kernel='rbf', class_weight='auto', gamma = 0.00001, C=1000000).fit(X_train, y_train)
    
    y_pred_one = dtc.predict(X_test)
    y_pred_two = srb.predict(X_test)
    y_pred_thr = rfc.predict(X_test)

    Tools.classification_report("DTC", y_test, y_pred_one, lab_use)
    Tools.classification_report("SVC", y_test, y_pred_two, lab_use)
    Tools.classification_report("RFC", y_test, y_pred_thr, lab_use)

    DRS = [dtc, rfc, srb]

    pickle.dump(DRS, dmp)

@main.command()
@click.option('--port', '-p',
    type = int,
    required = True,
    prompt = True,
    help = "UDP Broadcast Port Number"
)
@click.argument('dmp', type=click.File('rb'))
def f_test(dmp, port):
    DRS = pickle.load(dmp)

    @UDP.handler
    def svm_test(**kwargs):
        global buffer
        if 'dat' in kwargs:
            click.echo(".", nl=False)
            buffer.append(kwargs['dat']['accelerometer'])

        if len(buffer) == 100:
            buf_ftr = Routines.feature_vector(zip(*buffer))

            out = []

            for clsfr in DRS:
                out.append(clsfr.predict(buf_ftr))

            print(out)

    UDP.start_routine('', port)

if __name__ == "__main__":
    main()
