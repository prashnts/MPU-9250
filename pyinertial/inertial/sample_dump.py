#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class Samples(object):
    """
    Provides abstracted access to the raw dataset.
    Obtained from http://archive.ics.uci.edu/.

    This class abstracts the experiment number and user number and concatenates
    the resulting generator. The results may also be (by default) partitioned in
    moving windows, hence, there's no need for further sample processing.

    This class assumes that Dataset is located in /data/_inertial_db directory.
    This behaviour may be changed by changing the constant DATA_DIR.
    """

    DATA_DIR = "/data/_inertial_db/"
    LABLES = "labels.txt"
    ACCEL_FILE_FMT = "acc_exp{0}_user_{0}.txt"
    GYRO_FILE_FMT  = "gyro_exp{0}_user_{0}.txt"

    def __init__():
        pass

    def _load_label(self):
        """
        Loads the label data.
        """
        pass

    def _unpack_data(self, ):
        pass

    def _load_file(self, file_name):
        """
        Loads the file content from data directory.

        Args:
            file_name (str): File Name.
        Returns:
            (str): File Content.
        Raises:
            ValueError
        """

        try:
            path = self.DATA_DIR + file_name
            with open(path, "r") as minion:
                return minion.read()
        except FileNotFoundError:
            raise ValueError
