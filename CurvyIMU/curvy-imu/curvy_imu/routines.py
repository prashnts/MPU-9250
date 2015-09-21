#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
"""

import numpy as np

from numpy import linalg as LA
from scipy.optimize import curve_fit

from .helper import Helper

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

        return [np.absolute(_) for _ in eig_val[0:2]] + [sum(energy) / 16]
