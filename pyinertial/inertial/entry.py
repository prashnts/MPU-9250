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
#@click.argument('pickled_svm_object', type = click.File('rb'))
def scratch_f():
    s = Samples()
    # for i in s.LABEL_DICT:
    #     w = s.probe(i)
    #     a = itertools.chain(*w)
    #     plt.figure()
    #     x, y, z = list(zip(*a))
    #     d = pd.Series(x)
    #     print(i)
    #     autocorrelation_plot(d)
    #     plt.show()
    #while True:
    # Routines.feature_vector(zip(*next(w)))
    for i in s.LABEL_DICT:
        w = s.probe(i)
        print(i)
        Routines.feature_vector(zip(*next(w)))
