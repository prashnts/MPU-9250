#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import scipy.io as scio

a = scio.loadmat("tof-confidence-data/training-scenes/room/room_pmd_data.mat")

print(len(a['room_pmd_data'][0][0][0][199]))
print(a['room_pmd_data'][0][0][0][199])