#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
import math
import numpy as np

from scipy.optimize import curve_fit
from itertools import cycle

class Helper(object):
    """
    """

    #: (cycle) A circular queue to show progress.
    pool = cycle(["😀  ", "😃  ", "😄  "])

    @staticmethod
    def gather_class():
        """
        Gathers the Motion Class from User.
        """
        data_class_global = click.prompt('Motion Class Tag', type = str)

        if click.confirm('Proceed?'):
            return data_class_global
        else:
            gather_class()

    @staticmethod
    def concatenate(measurements):
        """
        Concatenates the measurements taken here.
        Example: concatenate(zip([[x1], [x2] ...], [[y1], [y2], ...]))
                 returns [[x1, y1], [x2, y2], ...]
        Args:
            measurements (zip): A zip concatenation of the measurements.
        Returns:
            generator: Generator instance containing the place wise concatenation of the measurements.
        """
        for i in measurements:
            result = []
            for j in i:
                for k in j:
                    result.append(k)
            yield result

    @staticmethod
    def curve_fit(transform_function, measurements):
        """
        Features are calculated out of a series of values.
        """
        x_values = np.array(range(0, len(measurements)))
        popt, pcov = curve_fit(transform_function, x_values, measurements)

        return list(popt)

    @staticmethod
    def load_csv(handle, column_delim = ","):
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

        for row in handle:
            column_data = row.rstrip().split(",")
            if len(column_data) == len(column_headers):
                dat_map = {column_headers[i]: float(column_data[i]) for i in range(0, len(column_headers))}
                yield dat_map

    @staticmethod
    def autocorrelation(x):
        """
        http://stackoverflow.com/q/14297012/190597
        http://en.wikipedia.org/wiki/Autocorrelation#Estimation
        """
        n = len(x)
        variance = np.var(x)
        x = x-np.mean(x)
        r = np.correlate(x, x, mode = 'full')[-n:]
        assert np.allclose(r, np.array([(x[:n-k]*x[-(n-k):]).sum() for k in range(n)]))
        result = r/(variance*(np.arange(n, 0, -1)))
        return result

    @staticmethod
    def discreet_wave_energy(l):
        """

        """

        def area_under(a, b):
            """
            Calculates absolute area contained below a straight line joining a and b from a to b.
            Mathematically, this is Integral(|line(x, a, b)|)dx from a to b.
            The integral is calculated numerically, with the precision defined by STEP_VAL (default: 0.01).
            STEP_VAL can be decreased for increased precision, however, it has number of times while loop is ran is 1/STEP_VAL, hence, this parameter must be changed manually - directly in source.
            Args:
                a (float): y1 value
                b (float): y2 value
            Returns:
                (float) Area
            """
            def line(x):
                """
                Using two - point equation for the straight line
                x1, and x2 are assumed to be 0 and 1 respectively due to parent.
                y - a = (b - a)x
                Args:
                    x (float): function variable
                Returns:
                    (float) y value at x
                """
                return ((b - a) * x - a)

            STEP_VAL = 0.01

            area = 0
            x = 0

            while x <= 1:
                area += STEP_VAL * abs(line(x))
                x += STEP_VAL

            return area

        pairs = zip(l[0::], l[1::])

        return sum([area_under(*_) for _ in pairs])

    def sine_wave_energy(m, n, a, b, c, d):
        """
        """

        def int_sine(x):
            """
            """
            return (b * d * x - a * np.cos(b * x + c)) * np.sign(a * np.sin(b * x + c) + d) / d

        return abs(int_sine(n) - int_sine(m))

class Stupidity(object):
    """
    Stupid Curve Approximation Methods, and Evaluations.
    """

    @staticmethod
    def sine_fit(val):
        """
        Approximates the Parameters for:
            f(x) = asin(bx + c) + d
        """

        #: Vertical Shift -> Mean
        d = sum(val) / len(val)

        #: Finds the number of oscillations (switches) from the mean axis. This estimates b.
        oscln = lambda x: x[0] > d > x[1] if x[0] > x[1] else x[1] > d > x[0]
        osc_cnt = list(map(oscln, zip(val[0::], val[1::]))).count(True)
        b = (osc_cnt * np.pi) / (1 * len(val))

        up_m = [_ for _ in val if _ > d]
        dn_m = [_ for _ in val if _ < d]

        up_mean = sum(up_m) / len(up_m)
        dn_mean = sum(dn_m) / len(dn_m)

        a = min([max(val) - d, d - min(val)])

        a = max([up_mean - d, d - dn_mean])
        a = up_mean - dn_mean

        #c = np.arcsin(-d / a)
        c = 0

        return (lambda x: a * np.sin(b * x + c) + d, [a, b, c, d])

    @staticmethod
    def arctan_fit(val):
        """
        """

        l = int(len(val) / 3)

        c1, c2, c3 = val[:l], val[l:len(val) - l], val[len(val) - l:]
        m1, m2, m3 = np.mean(c1), np.mean(c2), np.mean(c3)

        a = (m3 - m1) / 2
        b = 0
        c = int(len(val) / 2)
        d = np.mean(val)

        return (lambda x: a * np.arctan(x - c) + d, [a, b, c, d])

    @staticmethod
    def line_fit(val):
        """
        Fits approximate line in
        """
        m = 0
        c = np.mean(val)

        return (lambda x: c, [m, c])

    @staticmethod
    def frechet_dist(P, Q, remap = True):
        """
        Computes the discrete frechet distance between two polygonal lines
        Algorithm: http://www.kr.tuwien.ac.at/staff/eiter/et-archive/cdtr9464.pdf
        Obtained from: https://gist.github.com/MaxBareiss/ba2f9441d9455b56fbc9

        Args:
            P, Q (list or list of touples): Polygon lines 1 and 2. See `remap`.
            remap (bool, default: True): Remaps P and Q, if they are single dimensional points. If P and Q are touples of coordinates, set this flag to False.
        Returns:
            (float): Frechet Distance
        """

        def euc_dist(pt1, pt2):
            """
            Calculates the Euclidean Distance between n-dimensional vectors pt1 and pt2.
            Args:
                pt1, pt2 (list): n-Dimensional Vectors
            Returns:
                (float): Euclidean Distance
            Raises:
                ValueError: pt1 and pt2 are not comparable.
            """

            if len(pt1) is not len(pt2):
                raise ValueError

            coupling = [(ui - vi)**2 for (ui, vi) in zip(pt1, pt2)]

            return math.sqrt(sum(coupling))

        def _c(ca, i, j, P, Q):
            """
            Calculates the infinite norm of matrix `ca` recursively. The norm is the coupling here.
            """

            if ca[i, j] > -1:
                return ca[i, j]
            elif i == 0 and j == 0:
                ca[i, j] = euc_dist(P[0], Q[0])
            elif i > 0 and j == 0:
                ca[i, j] = max(_c(ca, i - 1, 0, P, Q), euc_dist(P[i], Q[0]))
            elif i == 0 and j > 0:
                ca[i, j] = max(_c(ca, 0, j - 1, P, Q), euc_dist(P[0], Q[j]))
            elif i > 0 and j > 0:
                ca[i, j] = max(min(_c(ca, i - 1, j, P, Q), _c(ca, i - 1, j - 1, P, Q), _c(ca, i, j - 1, P, Q)), euc_dist(P[i], Q[j]))
            else:
                ca[i, j] = float("inf")
            return ca[i, j]

        if remap:
            P = list(zip(range(len(P)), P))
            Q = list(zip(range(len(Q)), Q))

        ca = np.ones((len(P), len(Q)))
        ca = np.multiply(ca, -1)
        return _c(ca, len(P) - 1, len(Q) - 1, P, Q)
