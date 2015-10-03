#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import numpy as np
import matplotlib.pyplot as plt

from numpy import linalg as LA
from scipy.optimize import curve_fit
from scipy.signal import argrelmax, argrelmin

from .helper import Helper
from .helper import Stupidity
from .helper import Gradient

class Routines(object):
    """
    Wrapper for custom routine functions.
    Just coz Swag.
    """

    @staticmethod
    def sep_9_1242(x, y, z):
        """
        This method creates a feature in Four stages:
        1. Create overlapping chunks of the x, y, z axis data, 16 length.
        2. Fit individual axes on `y = aSin(bx + c) + d`.
        3. Create a 3x4 matrix, with each row having: [a, b, c, d].
        4. Remove column with parameter `d` (vertical shift) to get a 3x3 matrix.
        5. Yield the eigenvalue of the matrix - feature.

        Args:
            x (list): x axis probe data.
            y (list): y axis probe data.
            z (list): z axis probe data.

        Returns:
            (generator): 3D Feature Vector
        """

        #: Overlapped x, y, and z axis data.
        #  Data length -> 16
        x_o = zip(*[x[_:] for _ in range(16)])
        y_o = zip(*[y[_:] for _ in range(16)])
        z_o = zip(*[z[_:] for _ in range(16)])

        #: Gathers row wise data.
        row = zip(x_o, y_o, z_o)

        for val_set in row:
            yield Routines.sep_9_1242_feature(val_set)

    @staticmethod
    def sep_9_1242_feature(val_set):
        """
        Supplementary method for method `sep_9_1242`.
        It performs the subtask 2 to 5 for the previous method.
        It has been separated from parent method for modular usage while training the streaming data.

        Args:
            val_set (list): List containing the list of chunks of data.

        Returns:
            (list): Eigenvalues, feature.
        """

        def func(x, a, b, c, d):
            #: The fit-function
            #: y = aSin(bx + c) + d
            return a * np.sin(b * x + c) + d

        ftr = []
        for col in val_set:
            #: Curve fit each column to get the period, phase shift, vertical
            #: shift, and amplitude.
            try:
                #: if we find optimal fit, then append.
                popt = Helper.curve_fit(func, col)
                ftr.append(popt)
            except RuntimeError:
                #: Let it be (TM)
                #: To keep the structure of the `ftr` intact
                #  we do this stupid hack.
                ftr.append([0, 0, 0, 0])

        #: Yield a single feature, combining all of the above
        ftr_cmb = zip(*ftr)

        ampl  = next(ftr_cmb)   # Amplitude
        phase = next(ftr_cmb)   # Phase
        ph_sh = next(ftr_cmb)   # Phase Shift
        ve_sh = next(ftr_cmb)   # Vertical Shift

        eig_val, eig_vec = LA.eig([ampl, phase, ph_sh])

        return [np.absolute(_) for _ in eig_val]

    @staticmethod
    def sep_15_2332(x, y, z):
        """
        This method creates a feature in Four stages:
        1. Create overlapping chunks of the x, y, z axis data, 16 length.
        1.1 Calculate "wave" data.
        2. Fit individual axes on `y = aSin(bx + c) + d`.
        3. Create a 3x4 matrix, with each row having: [a, b, c, d].
        4. Remove column with parameter `d` (vertical shift) to get a 3x3 matrix.
        5. Yield the eigenvalue of the matrix - feature.

        Args:
            x (list): x axis probe data.
            y (list): y axis probe data.
            z (list): z axis probe data.

        Returns:
            (generator): 3D Feature Vector
        """

        #: Overlapped x, y, and z axis data.
        #  Data length -> 16
        x_o = zip(*[x[_:] for _ in range(16)])
        y_o = zip(*[y[_:] for _ in range(16)])
        z_o = zip(*[z[_:] for _ in range(16)])

        #: Gathers row wise data.
        row = zip(x_o, y_o, z_o)

        for val_set in row:
            yield Routines.sep_15_2332_feature(val_set)

    @staticmethod
    def sep_15_2332_feature(val_set):
        """
        Supplementary method for method `sep_9_1242`.
        It performs the subtask 2 to 5 for the previous method.
        It has been separated from parent method for modular usage while training the streaming data.

        Args:
            val_set (list): List containing the list of chunks of data.

        Returns:
            (list): Eigenvalues, feature.
        """

        def func(x, a, b, c, d):
            #: The fit-function
            #: y = aSin(bx + c) + d
            return a * np.sin(b * x + c) + d

        ftr = []
        energy = []
        for col in val_set:
            #: Curve fit each column to get the period, phase shift, vertical
            #: shift, and amplitude.
            try:
                #: if we find optimal fit, then append.
                popt = Helper.curve_fit(func, col)
                energy.append(Helper.discreet_wave_energy(col))
                ftr.append(popt)
            except RuntimeError:
                #: Let it be (TM)
                #: To keep the structure of the `ftr` intact
                #  we do this stupid hack.
                ftr.append([0, 0, 0, 0])

        #: Yield a single feature, combining all of the above
        ftr_cmb = zip(*ftr)

        ampl  = next(ftr_cmb)   # Amplitude
        phase = next(ftr_cmb)   # Phase
        ph_sh = next(ftr_cmb)   # Phase Shift
        ve_sh = next(ftr_cmb)   # Vertical Shift

        eig_val, eig_vec = LA.eig([ampl, phase, ve_sh])
        #eig_val = [np.var(ampl), np.var(phase), np.var(ph_sh)]

        return [np.absolute(_) for _ in eig_val] + [sum(energy) / 16]

    @staticmethod
    def sep_29(x, y, z):
        """
        This method creates a feature in Four stages:
        1. Create overlapping chunks of the x, y, z axis data, 16 length.
        2. Find Discreet Wave Energy
        3. Find Sine, Arctan, Line Fit
        4. Find Frechet Distances
        5. Find Perimeter
        6. Normalise DWE, Frechet Distance, and Perimeter
        7. Combine Feature Axes

        Args:
            x (list): x axis probe data.
            y (list): y axis probe data.
            z (list): z axis probe data.

        Returns:
            (generator): Feature Vector
        """

        #: Overlapped x, y, and z axis data.
        #  Data length -> 16
        x_o = list(zip(*[x[_:] for _ in range(64)]))[::10]
        y_o = list(zip(*[y[_:] for _ in range(64)]))[::10]
        z_o = list(zip(*[z[_:] for _ in range(64)]))[::10]
        #: Gathers row wise data.
        row = zip(x_o, y_o, z_o)

        for val_set in row:
            yield Routines.sep_29_feature(val_set)

    @staticmethod
    def sep_29_feature(val_set):
        """
        Supplementary method for method `sep_29`.
        Performs the subtask 2 to 7 for the previous method.

        Args:
            val_set (list): List containing the list of chunks of data.

        Returns:
            (list): Eigenvalues, feature.
        """

        print(val_set)

        ftr = []
        wave_energy = []
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_ylim([-4, 4])

        for col in val_set:
            discreet_fit = [Stupidity.sine_fit(col),
                            Stupidity.arctan_fit(col),
                            Stupidity.line_fit(col)]

            w_col   = len(col)

            wave_energy.append(Helper.discreet_wave_energy(col) / w_col)

            curves   = [map(_[0],  range(w_col)) for _ in discreet_fit]
            fre_dist = [Stupidity.frechet_dist(list(_), col) for _ in curves]

            n_fre_dist = Stupidity.normalise_dist(fre_dist)

            ftr.append(n_fre_dist)

            local_maxima = list(argrelmax(np.array(col), order = 5)[0])
            local_minima = list(argrelmin(np.array(col), order = 5)[0])

            for _ in local_maxima:
                ax.scatter(_, col[_], marker = '^')

            for _ in local_minima:
                ax.scatter(_, col[_], marker = '*')

            #ax.plot([discreet_fit[1][0](_) for _ in range(w_col)])
            ax.plot(col)
            keypoints = local_minima + local_maxima
            print(sorted(keypoints))

        plt.show()


        wave_en = sum(wave_energy) / 3
        ftr_nml = [max(_) for _ in zip(*ftr)]

        return ftr_nml + [wave_en]


    @staticmethod
    def sep_29_02_feature(val_set):
        """
        Supplementary method for method `sep_29`.
        Performs the subtask 2 to 7 for the previous method.

        Args:
            val_set (list): List containing the list of chunks of data.

        Returns:
            (list): Eigenvalues, feature.
        """

        ftr = []
        wave_energy = []
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.set_ylim([-4, 4])
        var1 = []
        slope = []

        for col in val_set:
            discreet_fit = [Stupidity.sine_fit(col),
                            Stupidity.arctan_fit(col),
                            Stupidity.line_fit(col)]

            w_col   = len(col)

            wave_energy.append(Helper.discreet_wave_energy(col) / w_col)

            curves   = [map(_[0],  range(w_col)) for _ in discreet_fit]
            fre_dist = [Stupidity.frechet_dist(list(_), col) for _ in curves]

            n_fre_dist = Stupidity.normalise_dist(fre_dist)

            ftr.append(n_fre_dist)

            local_maxima = list(argrelmax(np.array(col), order = 5)[0])
            local_minima = list(argrelmin(np.array(col), order = 5)[0])

            for _ in local_maxima:
                ax.scatter(_, col[_], marker = '^')

            for _ in local_minima:
                ax.scatter(_, col[_], marker = '*')

            #ax.plot([discreet_fit[1][0](_) for _ in range(w_col)])
            ax.plot(col)
            keypoints = sorted(local_minima + local_maxima)
            key_map = [col[_] for _ in keypoints]
            var1.append(np.var(key_map))

            key_map_t = [[_, col[_]] for _ in keypoints]
            polyg, m, lengt = Stupidity.polygon(key_map_t)
            bezier = Stupidity.cubic_bezier(key_map_t)
            slope.append(m)
            print(sum(lengt))
            gr = Gradient()
            grm = list(gr.remap(m))
            grc = set(grm)
            # print([[_, grm.count(_)] for _ in grc])
            #print(np.var(grm))
            ax.plot([polyg(_) for _ in range(w_col)])
            ax.plot([bezier(_) for _ in range(w_col)])

        sl_v = [np.var(_) for _ in slope]

        print( [sum(var1) / 3,
                sum(wave_energy) / 3,
                sum(sl_v) / 3,
                [[max(_), min(_)] for _ in slope]
             ])
        plt.show()

        wave_en = sum(wave_energy) / 3
        ftr_nml = [max(_) for _ in zip(*ftr)]

        return ftr_nml + [wave_en]
