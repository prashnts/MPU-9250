#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import click
import math
import numpy as np
import inspect

from scipy.optimize import curve_fit
from scipy.signal import argrelmax, argrelmin
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
        Finds the Discrete Wave energry (extrapolated points).

        Args:
            l (list): Points

        Returns:
            (float): Energy Representation
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

    @staticmethod
    def sine_wave_energy(m, n, a, b, c, d):
        """
        """

        def int_sine(x):
            """
            """
            return (b * d * x - a * np.cos(b * x + c)) * np.sign(a * np.sin(b * x + c) + d) / d

        return abs(int_sine(n) - int_sine(m))

    @staticmethod
    def sliding_window(sequence, win_size, step = 1):
        """
        Returns a generator that will iterate through
        the defined chunks of input sequence.
        Input sequence must be iterable.
        """

        if step > win_size:
            raise ValueError("step should be lesser than win_size")
        if win_size > len(sequence):
            raise ValueError("win_size should be lesser than length of sequence")

        # Pre-compute number of chunks to emit
        num_of_chunks = int((len(sequence) - win_size) / step) + 1
        # print(num_of_chunks)

        # Do the work
        for i in range(0, num_of_chunks * step, step):
            yield sequence[i:i + win_size]

    @staticmethod
    def pooled_variance(sequence):
        """
        Calculates the Pooled Variance of the given population.

        Args:
            sequence ([touples]): List of touples: [pop_variance, pop_size]
        Returns:
            (float): Pooled Variance
        """

        return sum([(l - 1) * v for v, l in sequence]) / sum([(l - 1) for _, l in sequence])

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
        val_ = list(val)
        c = val_.index(max(val_))

        return (lambda x: a * np.sin(b * x + c) + d, [a, b, c, d])

    @staticmethod
    def arctan_fit(val):
        """
        """

        l = int(len(val) / 3)

        c1, c2, c3 = val[:l], val[l:len(val) - l], val[len(val) - l:]
        m1, m2, m3 = np.mean(c1), np.mean(c2), np.mean(c3)

        #print(m1, m2, m3)

        a = (m3 - m1) / 2
        b = 0
        c = int(len(val) / 2)
        d = m1 - m3

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

        def _c(ca, i, j, P, Q):
            """
            Calculates the infinite norm of matrix `ca` recursively. The norm is the coupling here.
            """

            if ca[i, j] > -1:
                return ca[i, j]
            elif i == 0 and j == 0:
                ca[i, j] = Stupidity.euc_dist(P[0], Q[0])
            elif i > 0 and j == 0:
                ca[i, j] = max(_c(ca, i - 1, 0, P, Q), Stupidity.euc_dist(P[i], Q[0]))
            elif i == 0 and j > 0:
                ca[i, j] = max(_c(ca, 0, j - 1, P, Q), Stupidity.euc_dist(P[0], Q[j]))
            elif i > 0 and j > 0:
                ca[i, j] = max(min(_c(ca, i - 1, j, P, Q), _c(ca, i - 1, j - 1, P, Q), _c(ca, i, j - 1, P, Q)), Stupidity.euc_dist(P[i], Q[j]))
            else:
                ca[i, j] = float("inf")
            return ca[i, j]

        if remap:
            P = list(zip(range(len(P)), P))
            Q = list(zip(range(len(Q)), Q))

        ca = np.ones((len(P), len(Q)))
        ca = np.multiply(ca, -1)
        return _c(ca, len(P) - 1, len(Q) - 1, P, Q)

    @staticmethod
    def normalise_dist(l):
        n_f = lambda x: 1 - (x / sum(l))
        return list(map(n_f, l))

    @staticmethod
    def polygon(l):
        """
        Returns generalised polygonal function from the given set of points.
        """

        slope = []
        lengt = []

        def line(p1, p2):
            """
            Returns a line function passing through p1 and p2.
            y - y1 = (y2 - y1) / (x2 - x1) * (x - x1)
            or   y = (y2 - y1) / (x2 - x1) * (x - x1) + y1

            Args:
                p1, p2 (List): Point 1 and Point 2
            Returns:
                (callable): Line function
            """
            m = (p2[1] - p1[1]) / (p2[0] - p1[0])
            c = p1[1] - m * p1[0]
            slope.append(m)
            lengt.append(Stupidity.euc_dist(p1, p2))

            return lambda x: m * x + c

        point_pairs = zip(l[0:], l[1:])
        fun = []

        for pair in point_pairs:
            fun.append([range(pair[0][0], pair[1][0]), line(*pair)])

        def func(x):
            for i in fun:
                if x in i[0]:
                    return i[1](x)
            return 0

        return func, slope, lengt

    @staticmethod
    def cubic_bezier(l):
        """
        """

        def cubic_func(p1, p2):
            m = (p2[1] - p1[1]) / (p2[0] - p1[0])
            c = p1[1] - m * p1[0]
            a = p1[0]
            b = p2[0]

            d = m - (m * (b**2 + a * b + a**2) / 6) - (c * (b + a) / 2)
            k = (m * a * (b**2 + a * b) / 6) + (a * b * c / 2) + c

            return lambda x: (m * x**3 / 6) + (c * x**2 / 2) + (d * x) + k

        def bezier(points):
            A = []
            B = []
            for i in points:
                x, y = i
                A.append([x**3, x**2, x, 1])
                B.append(y)
            a, b, c, d = list(np.linalg.solve(np.array(A), np.array(B)))
            return lambda x: a * x**3 + b * x**2 + c * x + d

        # point_pairs = zip(l[0:], l[1:])
        fun = []

        control_points = Helper.sliding_window(l, 4, 1)

        for w in control_points:
            fun.append([range(w[0][0], w[1][0]), bezier(w)])

        # for pair in point_pairs:
        #     fun.append([range(pair[0][0], pair[1][0]), cubic_func(*pair)])

        def func(x):
            for i in fun:
                if x in i[0]:
                    return i[1](x)
            return 0

        return func

    @staticmethod
    def extrema_keypoints(l):
        """
        Finds the Extremities of the discrete wave sequence.
        Extremities are defined as the first and last points, the local maxima and the local minima.
        Args:
            l
        """
        l_maxima  = list(argrelmax(np.array(l), order = 3)[0])
        l_minima  = list(argrelmin(np.array(l), order = 3)[0])
        collation = sorted(l_minima + l_maxima)
        keypoints = [[_, l[_]] for _ in collation]

        #: Handle Edge cases
        f = [0, l[0]]
        l = [len(l), l[len(l) - 1]]

        #: Append Extremities
        keypoints.insert(0, f)
        keypoints.append(l)

        return keypoints

    @staticmethod
    def normal_destribution(l):
        """
        Figures out if a given list of raw values is distributed normally.
        """
        pass

    @staticmethod
    def nbin(l, n = 3, paired = True):
        """
        Divides `l` (list) into n Bins.

        Args:
            l (list): List
            n (int): Default 3. Number of Bins to divide l into
            paired (bool): Default True. Returns the ordered pair with x centre
                of the chunks.
        Returns:
            (generator): Iterable of list chunks.

        Notes:
            If the length of list is not divisible by n, the list is
            truncated with reminder(len/n)
        """

        c = math.floor(len(l) / n)
        d = math.floor(len(l) / c)
        e = math.floor(len(l) / (2 * n))

        for i in range(0, d):
            y = l[i * c:(i + 1) * c]
            x = ((2 * i) + 1) * e
            yield (x, y) if paired is True else y

    @staticmethod
    def nmethod(l, n, func):
        """
        Maps `func` to nbins returned by Stupidity.nbin, and returns ordered
        pairs of (x, func(y)).

        Args:
            See Stupidity.nbin
            func (callable): The Map function. MUST only accept a list.

        Returns:
            (generator): Mapped iterable.
        """

        points = Stupidity.nbin(l, n)
        for x, y in points:
            yield (x, func(y))

    @staticmethod
    def three_var(l):
        """
        Calculates three gradient of list using nmethod.
        """
        chunks = list(Stupidity.nbin(l, 3, False))
        return [np.log(np.var(chunks)), 3]

    @staticmethod
    def three_grad_bin(l):
        """
        Calculates three gradient of list using nmethod.
        """
        chunks = list(Stupidity.nbin(l, 3, False))
        return [np.log(np.var(chunks)), 3]

    @staticmethod
    def dominant_axis(en):
        """
        """
        return en.index(max(en))

class Gradient(object):

    def __init__(self, r = 3):
        self.bins = Gradient.gradient_bin(r)

    @staticmethod
    def gradient_bin(r):
        """
        Creates the Gradient Bin Estimator. Divides -90 to 90 degrees into equal intervals, and estimates the slope intervals.
        Args:
            r (int): Step value in degrees.
        Returns:
            (list): Format [Bin_Number, Callable]

        Example: If one wishes to create gradient bins spaced at 10 degrees, call `gradient_bin(10)`.
        """

        #: If r = 5 degrees, range(-17, 18) => [-17, 17].
        intrvl_v = [np.tan(np.radians(r * _)) for _ in range(int(-90 / r) + 1, int(90 / r))]
        #: Handle corner cases.
        intrvl_v.insert(0, float("-inf"))
        intrvl_v.append(float("inf"))
        intrvl_pair = list(zip(intrvl_v[0:], intrvl_v[1:]))

        #: Rule Estimators
        #: `_=_` Captures _ in lambda closure, hence allowing reuse.
        rules = [lambda x, _=_: _[0] <= x < _[1] for _ in intrvl_pair]

        #: Remap Estimator
        bins = zip(range(int(-90 / r), int(90 / r) + 1), rules)

        return list(bins)

    def bin(self, m):
        """
        """

        for rule in self.bins:
            if rule[1](m):
                return rule[0]

        raise ValueError

    def remap(self, m):
        """
        """
        return list(map(self.bin, m))
