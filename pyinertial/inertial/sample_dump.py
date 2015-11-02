#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import linecache
import json
import click

from .helper import Helper

WINDOWLEN = 100
STEP = 20

class UCI(object):
    """
    Provides abstracted access to the raw dataset.
    Obtained from http://archive.ics.uci.edu/.

    This class abstracts the experiment number and user number and concatenates
    the resulting generator. The results may also be (by default) partitioned in
    moving windows, hence, there's no need for further sample processing.

    This class assumes that Dataset is located in /data/_inertial_db directory.
    This behaviour may be changed by changing the constant DATA_DIR.
    """

    DATA_DIR = "/data/_inertial_db/UCI/"
    LABLES = "labels.txt"
    ACCEL_FILE_FMT = "acc_exp{0}_user{1}.txt"
    GYRO_FILE_FMT  = "gyro_exp{0}_user{1}.txt"
    LABEL_DICT = {
        "WALKING":              "1",
        "WALKING_UPSTAIRS":     "2",
        "WALKING_DOWNSTAIRS":   "3",
        "SITTING":              "4",
        "STANDING":             "5",
        "LAYING":               "6",
        "STAND_TO_SIT":         "7",
        "SIT_TO_STAND":         "8",
        "SIT_TO_LIE":           "9",
        "LIE_TO_SIT":           "10",
        "STAND_TO_LIE":         "11",
        "LIE_TO_STAND":         "12",
    }
    LABEL_DICT_USED = {
        "WALKING":              "1",
        "WALKING_UPSTAIRS":     "2",
        "WALKING_DOWNSTAIRS":   "3",
        "SITTING":              "4",
        "STANDING":             "5",
        #"LAYING":               "6",
    }

    def __init__(self):
        self._load_label()

    def probe(self, tag, window_len = WINDOWLEN, step = STEP):
        """
        """

        lz = lambda x: x.zfill(2)
        for meta in self.labels[self.LABEL_DICT[tag]]:
            file_name = self.DATA_DIR + self.ACCEL_FILE_FMT.format(lz(meta[0]), lz(meta[1]))
            line = lambda x: linecache.getline(file_name, x).rstrip().split(" ")

            conc_dat = []

            for i in range(int(meta[2]), int(meta[3]) + 1):
                l = line(i)
                if len(l) == 3:
                    conc_dat.append([float(_) for _ in l])

            windows = Helper.sliding_window(conc_dat, window_len, step)

            yield from windows

    def _load_label(self):
        """
        Loads the label data.
        """
        label_dat = self._load_file(self.LABLES)
        self.labels = {__: list() for (_, __) in self.LABEL_DICT.items()}

        for i in label_dat:
            self.labels[i.pop(2)].append(i)

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
                for line in minion:
                    yield line.rstrip().split(" ")

        except FileNotFoundError:
            raise ValueError

class Twenté(object):
    """
    Provides access to the dataset from Twenté university.

    See `UCI` for more details.
    """
    DATA_DIR = "/data/_inertial_db/Twente/"
    LABLES = "labels.json"

    LABELS = ["WALKING", "RUNNING", "SITTING", "STANDING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS"]

    LABEL_DICT_USED = {
        "WALKING":              "1",
        "WALKING_UPSTAIRS":     "2",
        "WALKING_DOWNSTAIRS":   "3",
        "SITTING":              "4",
        "STANDING":             "5",
        "RUNNING":              "6",
    }

    def __init__(self):
        self._load_label()

    def _load_label(self):
        with open(self.DATA_DIR + self.LABLES) as minion:
            self.labels = json.loads(minion.read())

    def probe(self, tag, window_len = WINDOWLEN, step = STEP):
        """
        """
        conc_dat = []

        for fdat, rng in self.labels[tag].items():
            file_name = self.DATA_DIR + fdat
            line = lambda x: linecache.getline(file_name, x).rstrip().split(",")[1:4]

            for r in rng:
                conc_dat[:] = []
                for i in range(r[0], r[1] + 1):
                    l = line(i)
                    if len(l) == 3:
                        conc_dat.append([float(_) / 10 for _ in l])
                windows = Helper.sliding_window(conc_dat, window_len, step)
                yield from windows

class TwentéTwo(Twenté):
    """
    Provides access to the dataset from Twenté university.

    See `Twenté` for more details.
    """

    DATA_DIR = "/data/_inertial_db/TwenteTwo/"

    LABELS = ["WALKING", "JOGGING", "SITTING", "STANDING", "WALKING_UPSTAIRS", "WALKING_DOWNSTAIRS", "BIKING"]

    LABEL_DICT_USED = {
        "WALKING":              "1",
        "WALKING_UPSTAIRS":     "2",
        "WALKING_DOWNSTAIRS":   "3",
        "SITTING":              "4",
        "STANDING":             "5",
        "JOGGING":              "6",
        "BIKING":               "7",
    }

LabelDict = {
    "WALKING":              "1",
    "WALKING_UPSTAIRS":     "2",
    "WALKING_DOWNSTAIRS":   "3",
    "SITTING":              "4",
    "STANDING":             "5",
    "RUNNING":              "6",
    "JOGGING":              "7",
    "BIKING":               "8",
}
Labels = [
    "WALKING",
    "WALKING_UPSTAIRS",
    "WALKING_DOWNSTAIRS",
    "SITTING",
    "STANDING",
    "RUNNING",
    "JOGGING",
    "BIKING",
]
LabelDictC = {
    "WALKING":              "1",
    "WALKING_UPSTAIRS":     "1",
    "WALKING_DOWNSTAIRS":   "1",
    "SITTING":              "2",
    "STANDING":             "2",
    "RUNNING":              "3",
}

LabelsC = [
    "WALKING",
    "STATIONARY",
    "RUNNING",
]

LabelDictD = {
    "WALKING":              "1",
    "WALKING_UPSTAIRS":     "1",
    "WALKING_DOWNSTAIRS":   "1",
    "SITTING":              "2",
    "STANDING":             "2",
    "RUNNING":              "3",
    "BIKING":               "4",
    "JOGGING":              "5",
}
LabelsD = [
    "WALKING",
    "STATIONARY",
    "RUNNING",
    "BIKING",
    "JOGGING",
]
LabelDictE = {
    "WALKING":              "1",
    "WALKING_UPSTAIRS":     "2",
    "WALKING_DOWNSTAIRS":   "2",
    "SITTING":              "3",
    "STANDING":             "3",
    "RUNNING":              "4",
    "BIKING":               "5",
    "JOGGING":              "6",
}
LabelsE = [
    "WALKING",
    "STAIR",
    "STATIONARY",
    "RUNNING",
    "BIKING",
    "JOGGING",
]

def ChainProbes(tag, **kwargs):
    uci = UCI()
    twn = Twenté()
    twn2 = TwentéTwo()

    click.echo("Yielding UCI")
    if tag in uci.LABEL_DICT_USED:
        yield from uci.probe(tag, **kwargs)

    click.echo("Yielding Twenté")
    if tag in twn.LABELS:
        yield from twn.probe(tag, **kwargs)

    click.echo("Yielding Twenté Two")
    if tag in twn2.LABELS:
        yield from twn2.probe(tag, **kwargs)
