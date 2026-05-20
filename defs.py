import numpy as np
import math
from tqdm import tqdm
from datetime import datetime
import os

#Initial constants, S.I.:
G = 6.67430e-11
#Venus - perihelion data:
VENUS_RADIUS = 1
VENUS_MASS = 4.87e24
VENUS_R0_P = np.array([1.082e11, 0.0])
VENUS_V0_P = np.array([0.0, 35020.0])
#Earth - initial phase = 0:
EARTH_RADIUS = 1
EARTH_MASS = 5.97e24
EARTH_R0 = np.array([1.47e11, 0.0])
EARTH_V0 = np.array([0.0, 30300.0])
#Sun:
SUN_RADIUS = 1
SUN_MASS = 1.989e30
SUN_R0 = np.zeros(2)
SUN_V0 = np.zeros(2)

class Body:
    def __init__(self, name, mass, pos, vel):
        self.name = name
        self.mass = mass
        # phase: float
        # radius: float
        # distance: float #(to Sun)
        self.pos = np.array(pos, dtype='float64')
        self.vel = np.array(vel, dtype='float64')