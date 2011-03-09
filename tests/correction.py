#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011, Florent Lamiraux, Thomas Moulard, JRL, CNRS/AIST
#
# This file is part of sot-motion-planner.
# sot-motion-planner is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# sot-motion-planner is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Lesser Public License for more details.  You should have
# received a copy of the GNU Lesser General Public License along with
# sot-motion-planner. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import numpy as np
from math import acos, atan2, cos, sin, pi, sqrt

from dynamic_graph import plug
from dynamic_graph.sot.motion_planner import Localizer, Correction

from dynamic_graph.sot.dynamics.hrp2 import Hrp2Laas

try:
    from dynamic_graph.sot.core import OpPointModifior
    OpPointModifier = OpPointModifior
except ImportError:
    from dynamic_graph.sot.core import OpPointModifier

from dynamic_graph.sot.core import FeatureVisualPoint

def makePosition(tx, ty, tz):
    return ((1., 0., 0., tx),
            (0., 1., 0., ty),
            (0., 0., 1., tz),
            (0., 0., 0., 1.))


correction = Correction('correction')

correction.trajectoryLeftFootIn.value = makePosition(0., 0., 0.)
correction.trajectoryRightFootIn.value = makePosition(0., 0., 0.)
correction.trajectoryComIn.value = (0., 0.)

correction.offset.value = (1., 2., 0.)

t = 0
for i in xrange(2 * (1. / 0.005)):
    correction.trajectoryLeftFoot.recompute(t)
    correction.trajectoryRightFoot.recompute(t)
    correction.trajectoryCom.recompute(t)

    #print(np.matrix(correction.trajectoryLeftFoot.value))
    #print(np.matrix(correction.trajectoryRightFoot.value))
    #print(np.matrix(correction.trajectoryCom.value))
    print (np.matrix(correction.trajectoryLeftFoot.value)[0,3])
    print (np.matrix(correction.trajectoryLeftFoot.value)[1,3])
    print("---")

    correction.offset.value = (0., 0., 0)

    t += 1