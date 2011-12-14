#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2011, Florent Lamiraux, Thomas Moulard, JRL, CNRS/AIST
#
# This file is part of dynamic-graph.
# dynamic-graph is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# dynamic-graph is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Lesser Public License for more details.  You should have
# received a copy of the GNU Lesser General Public License along with
# dynamic-graph. If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
from dynamic_graph import plug
from dynamic_graph.sot.core import FeatureGeneric, TaskPD, RobotSimu
from dynamic_graph.sot.core.feature_position import FeaturePosition

from dynamic_graph.sot.motion_planner.feet_follower import FeetFollowerRos

from dynamic_graph.sot.motion_planner.math import *
from dynamic_graph.sot.motion_planner.motion_plan.tools import *

from dynamic_graph.sot.motion_planner.motion_plan.motion.abstract import *

class MotionWalkRos(Motion):
    yaml_tag = u'walk-ros'

    initialGain = 175.

    def __init__(self, motion, yamlData, defaultDirectories):
        checkDict('ros-parameter', yamlData)
        checkDict('interval', yamlData)

        Motion.__init__(self, motion, yamlData)

        self.name = id(yamlData)

        self.rosParameter = yamlData['ros-parameter']

        self.initialLeftAnklePosition = \
            self.robot.features['left-ankle'].reference.value
        self.initialRightAnklePosition = \
            self.robot.features['right-ankle'].reference.value

        self.feetFollower = FeetFollowerRos(
            "{0}_feet_follower".format(self.name))
        self.setAnklePosition()
        self.setInitialFeetPosition()
        print("Parsing trajectory...")
        self.feetFollower.parseTrajectory(self.rosParameter)
        print("done.")

        # Center of mass features and task.
        (self.featureCom, self.featureComDes, self.comTask) = \
            self.robot.createCenterOfMassFeatureAndTask(
            '{0}_feature_com'.format(self.name),
            '{0}_feature_ref_com'.format(self.name),
            '{0}_task_com'.format(self.name),
            selec = '111',
            gain = self.initialGain)

        # Make sure the CoM is converging toward the starting
        # CoM of the trajectory.
        self.featureComDes.errorIN.value = \
            (0., 0., self.robot.dynamic.com.value[2])


        # Operational points features/tasks.
        self.features = dict()
        self.tasks = dict()
        for op in ['left-ankle', 'right-ankle', 'waist']:
            (self.features[op], self.tasks[op]) = \
                self.robot.createOperationalPointFeatureAndTask(
                op, '{0}_feature_{1}'.format(self.name, op),
                '{0}_task_{1}'.format(self.name, op),
                gain = self.initialGain)

        # Plug the feet follower output signals.
        plug(self.feetFollower.zmp, self.robot.device.zmp)

        plug(self.feetFollower.com, self.featureComDes.errorIN)
        plug(self.feetFollower.signal('left-ankle'),
             self.features['left-ankle'].reference)
        plug(self.feetFollower.signal('right-ankle'),
             self.features['right-ankle'].reference)

        # Plug velocities into TaskPD.
        plug(self.feetFollower.comVelocity, self.comTask.errorDot)
        for op in ['left-ankle', 'right-ankle']:
            plug(self.feetFollower.signal(op + 'Velocity'),
                 self.tasks[op].errorDot)
        plug(self.feetFollower.waistYawVelocity,
             self.tasks['waist'].errorDot)

        # Initialize the waist yaw task.
        self.features['waist'].selec.value = '111000'
        plug(self.feetFollower.waistYaw, self.features['waist'].reference)
        self.tasks['waist'].controlGain.value = self.initialGain


        unlockedDofsRleg = []
        unlockedDofsLleg = []
        for i in xrange(6):
            #FIXME: HRP-2 specific
            unlockedDofsRleg.append(6 + i)
            unlockedDofsLleg.append(6 + 6 + i)


        # Push the tasks into supervisor.
        if not 'control' in motion.plan or not motion.plan['control']:
            motion.supervisor.addFeetFollowerStartCall(
                self.feetFollower.name,
                self.interval[0])

        motion.supervisor.addTask(self.comTask.name,
                                  self.interval[0], self.interval[1],
                                  self.priority + 3,
                                 tuple(self.extraUnlockedDofs))
        motion.supervisor.addTask(self.tasks['left-ankle'].name,
                                  self.interval[0], self.interval[1],
                                  self.priority + 2,
                                  tuple(unlockedDofsLleg))
        motion.supervisor.addTask(self.tasks['right-ankle'].name,
                                  self.interval[0], self.interval[1],
                                  self.priority + 1,
                                  tuple(unlockedDofsRleg))
        motion.supervisor.addTask(self.tasks['waist'].name,
                                  self.interval[0], self.interval[1],
                                  self.priority,
                                  ())

    def __str__(self):
        fmt = "walking motion ROS"
        return fmt

    def setupTrace(self, trace):
        print("setup trace for walk_ros")
        # Feet follower
        for s in ['zmp', 'waist',
                  'com', 'left-ankle', 'right-ankle', 'waistYaw',
                  'comVelocity', 'left-ankleVelocity',
                  'right-ankleVelocity', 'waistYawVelocity']:
            self.robot.addTrace(self.feetFollower.name, s)

    def canStart(self):
        return True #FIXME:

    def setAnklePosition(self):
        # Setup feet to ankle transformation.
        anklePosL = self.robot.dynamic.getAnklePositionInFootFrame()
        anklePosR = (anklePosL[0], -anklePosL[1], anklePosL[2])

        self.feetFollower.setLeftFootToAnkle(translationToSE3(anklePosL))
        self.feetFollower.setRightFootToAnkle(translationToSE3(anklePosR))

    def setInitialFeetPosition(self):
        self.feetFollower.setInitialLeftAnklePosition(
            self.initialLeftAnklePosition)
        self.feetFollower.setInitialRightAnklePosition(
            self.initialRightAnklePosition)
