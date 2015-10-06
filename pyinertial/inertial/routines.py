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

import pandas as pd

class Routines(object):
    """
    Wrapper for custom routine functions.
    Just coz Swag.
    """
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

            key_map_t = Stupidity.extrema_keypoints(col)
            colb = [[_, col[_]] for _ in range(len(col))]
            # key_map_t = [[_, col[_]] for _ in keypoints]
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
            #ax.plot([bezier(_) for _ in range(w_col)])

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

    @staticmethod
    def feature_vector(axes_data):
        """
        Creates the Feature Vector.
        Feature Vectors:
            - Wave Energy: Sum over all Axes
            - Keypoints: Local Maxima, Local Minima, Extrema
                - Variance
                - Polygon
                    - Variance of Gradient
                    - Gradient Bin Mode
                    - Binned Gradient Three Window Mode
                    - Weighted Variance
            - Moving Mean

        Args:
            axes_data (list): List containing chunks of data per axes.

        Returns:
            (list): Feature Vector
        """

        WINDOW_LEN = 5
        wave_energy = []
        gradient_bin = Gradient()
        variance = {_: [] for _ in ["gradient", "gradient_binned", "keypoint", "moving_mean_v", "ax_var", "sm_keypoint", "sm_gradient", "sm_gradient_binned"]}

        for ax_dat in axes_data:
            plt.ylim([-2, 2])
            wave_energy.append(Helper.discreet_wave_energy(ax_dat))
            keypoints = Stupidity.extrema_keypoints(ax_dat)

            variance["keypoint"].append([np.var(list(zip(*keypoints))[1]), len(keypoints)])

            polygon, slopes, lengths = Stupidity.polygon(keypoints)
            slope_binned = gradient_bin.remap(slopes)

            variance["gradient"].append([np.var(slopes), len(slopes)])
            variance["gradient_binned"].append([np.var(slope_binned), len(slope_binned)])

            variance["ax_var"].append([np.var(ax_dat), len(ax_dat)])

            b = pd.Series(ax_dat)
            b.plot(style='k--')

            rm = pd.rolling_mean(b, WINDOW_LEN)
            rolling_list = list(rm)[WINDOW_LEN - 1:]

            variance["moving_mean_v"].append(np.var(rolling_list))

            sm_keypoints = Stupidity.extrema_keypoints(rolling_list)
            variance["sm_keypoint"].append([np.var(list(zip(*sm_keypoints))[1]), len(sm_keypoints)])

            sm_polygon, sm_slopes, sm_lengths = Stupidity.polygon(sm_keypoints)
            sm_slope_binned = gradient_bin.remap(slopes)

            variance["sm_gradient"].append([np.var(sm_slopes), len(sm_slopes)])
            variance["sm_gradient_binned"].append([np.var(sm_slope_binned), len(sm_slope_binned)])

        print(variance)

        pass
