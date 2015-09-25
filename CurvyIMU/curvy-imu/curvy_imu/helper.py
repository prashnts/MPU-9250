#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
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