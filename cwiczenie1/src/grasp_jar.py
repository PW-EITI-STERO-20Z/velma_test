#!/usr/bin/env python2

## Runs test for motions in cart_imp mode.
# @ingroup integration_tests
# @file test_cimp_pose.py
# @namespace scripts.test_cimp_pose Integration test

# Copyright (c) 2017, Robot Control and Pattern Recognition Group,
# Institute of Control and Computation Engineering
# Warsaw University of Technology
#
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Warsaw University of Technology nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL <COPYright HOLDER> BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Dawid Seredynski
#

import roslib; roslib.load_manifest('velma_task_cs_ros_interface')
import rospy
import math

from velma_common import *
from rcprg_planner import *
from rcprg_ros_utils import exitError

if __name__ == "__main__":
    rospy.init_node('grasp_jar')

    rospy.sleep(0.5)
    br = tf.TransformBroadcaster()

    print "Running python interface for Velma..."
    velma = VelmaInterface()
    print "Waiting for VelmaInterface initialization..."
    if not velma.waitForInit(timeout_s=10.0):
        print "Could not initialize VelmaInterface\n"
        exitError(1)
    print "Initialization ok!\n"

    diag = velma.getCoreCsDiag()
    if not diag.motorsReady():
        print "Motors must be homed and ready to use for this test."
        exitError(1)

    if velma.enableMotors() != 0:
        exitError(14)

    while not rospy.is_shutdown():
        T_B_S = velma.getTf("B", "sloik")
        T_B_S2 = T_B_S * PyKDL.Frame(PyKDL.Rotation.RotZ(30.0/180.0*math.pi), PyKDL.Vector(-0.1,-0.1,0.2))

        br.sendTransform((T_B_S2.p.x(), T_B_S2.p.y(), T_B_S2.p.z()),
                         T_B_S2.M.GetQuaternion(),
                         rospy.Time.now(),
                         "sloik2",
                         "world")

        rospy.sleep(0.1)

    '''
    print "Switch to jnt_imp mode (no trajectory)..."
    velma.moveJointImpToCurrentPos(start_time=0.2)
    error = velma.waitForJoint()
    if error != 0:
        print "The action should have ended without error, but the error code is", error
        exitError(3)

    rospy.sleep(0.5)
    diag = velma.getCoreCsDiag()
    if not diag.inStateJntImp():
        print "The core_cs should be in jnt_imp state, but it is not"
        exitError(3)

    print "Checking if the starting configuration is as expected..."
    rospy.sleep(0.5)
    js = velma.getLastJointState()
    if not isConfigurationClose(q_map_starting, js[1], tolerance=0.2):
        print "This test requires starting pose:"
        print q_map_starting
        exitError(10)

    # get initial configuration
    js_init = velma.getLastJointState()

    planAndExecute(q_map_1)

    print "Switch to cart_imp mode (no trajectory)..."
    if not velma.moveCartImpRightCurrentPos(start_time=0.2):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)

    rospy.sleep(0.5)

    diag = velma.getCoreCsDiag()
    if not diag.inStateCartImp():
        print "The core_cs should be in cart_imp state, but it is not"
        exitError(3)

    print "Reset tools for both arms..."
    T_B_Wr = velma.getTf("B", "Wr")
    T_B_Wl = velma.getTf("B", "Wl")
    if not velma.moveCartImpRight([T_B_Wr], [0.1], [PyKDL.Frame()], [0.1], None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if not velma.moveCartImpLeft([T_B_Wl], [0.1], [PyKDL.Frame()], [0.1], None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    if velma.waitForEffectorLeft() != 0:
        exitError(9)

    print "Moving right wrist to pose defined in world frame..."
    T_B_Trd = PyKDL.Frame(PyKDL.Rotation.Quaternion( 0.0 , 0.0 , 0.0 , 1.0 ), PyKDL.Vector( 0.7 , -0.3 , 1.3 ))
    if not velma.moveCartImpRight([T_B_Trd], [3.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)
    print "calculating difference between desiread and reached pose..."
    T_B_T_diff = PyKDL.diff(T_B_Trd, velma.getTf("B", "Tr"), 1.0)
    print T_B_T_diff
    if T_B_T_diff.vel.Norm() > 0.05 or T_B_T_diff.rot.Norm() > 0.05:
        exitError(10)


    print "Rotating right writs by 30 deg around local z axis (right-hand side matrix multiplication)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = T_B_Tr * PyKDL.Frame(PyKDL.Rotation.RotZ(30.0/180.0*math.pi))
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around local y axis (right-hand side matrix multiplication)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = T_B_Tr * PyKDL.Frame(PyKDL.Rotation.RotY(30.0/180.0*math.pi))
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around local x axis (right-hand side matrix multiplication)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = T_B_Tr * PyKDL.Frame(PyKDL.Rotation.RotX(30.0/180.0*math.pi))
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    planAndExecute(q_map_1)

    print "Moving right wrist to pose defined in world frame..."
    T_B_Trd = PyKDL.Frame(PyKDL.Rotation.Quaternion( 0.0 , 0.0 , 0.0 , 1.0 ), PyKDL.Vector( 0.7 , -0.3 , 1.3 ))
    if not velma.moveCartImpRight([T_B_Trd], [3.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)
    print "calculating difference between desiread and reached pose..."
    T_B_T_diff = PyKDL.diff(T_B_Trd, velma.getTf("B", "Tr"), 1.0)
    print T_B_T_diff
    if T_B_T_diff.vel.Norm() > 0.05 or T_B_T_diff.rot.Norm() > 0.05:
        exitError(10)


    print "Rotating right writs by 30 deg around global z axis (left-hand side matrix multiplication)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Tr_old = T_B_Tr
    T_B_Trd = PyKDL.Frame(PyKDL.Rotation.RotZ(30.0/180.0*math.pi)) * T_B_Tr
    if not velma.moveCartImpRight([T_B_Trd], [3.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Moving right wrist to the previous pose (cart_imp)..."
    if not velma.moveCartImpRight([T_B_Tr_old], [3.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around global z axis (left-hand side matrix multiplication for rotation only, position is constant)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = PyKDL.Frame( PyKDL.Rotation.RotZ(30.0/180.0*math.pi) * T_B_Tr.M, T_B_Tr.p )
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around global y axis (left-hand side matrix multiplication for rotation only, position is constant)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = PyKDL.Frame( PyKDL.Rotation.RotY(30.0/180.0*math.pi) * T_B_Tr.M, T_B_Tr.p )
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around global x axis (left-hand side matrix multiplication for rotation only, position is constant)"
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = PyKDL.Frame( PyKDL.Rotation.RotX(30.0/180.0*math.pi) * T_B_Tr.M, T_B_Tr.p )
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), start_time=0.5):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    rospy.sleep(0.5)

    planAndExecute(q_map_1)

    print "Switch to cart_imp mode (no trajectory)..."
    if not velma.moveCartImpRightCurrentPos(start_time=0.2):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)

    print "Rotating right writs by 45 deg around local z axis and left wrist by -45 deg (right-hand side matrix multiplication)"
    synchronized_time = rospy.Time.now() + rospy.Duration(0.5)
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = T_B_Tr * PyKDL.Frame(PyKDL.Rotation.RotZ(30.0/180.0*math.pi))
    T_B_Tl = velma.getTf("B", "Tl")
    T_B_Tld = T_B_Tl * PyKDL.Frame(PyKDL.Rotation.RotZ(-30.0/180.0*math.pi))
    if not velma.moveCartImpRight([T_B_Trd], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if not velma.moveCartImpLeft([T_B_Tld], [2.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    if velma.waitForEffectorLeft() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating both writs by 30 deg around local x axis (right-hand side matrix multiplication)"
    synchronized_time = rospy.Time.now() + rospy.Duration(0.5)
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = T_B_Tr * PyKDL.Frame(PyKDL.Rotation.RotX(30.0/180.0*math.pi))
    T_B_Tl = velma.getTf("B", "Tl")
    T_B_Tld = T_B_Tl * PyKDL.Frame(PyKDL.Rotation.RotX(30.0/180.0*math.pi))
    if not velma.moveCartImpRight([T_B_Trd, T_B_Tr], [2.0, 4.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if not velma.moveCartImpLeft([T_B_Tld, T_B_Tl], [2.0, 4.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    if velma.waitForEffectorLeft() != 0:
        exitError(9)
    rospy.sleep(0.5)

    print "Rotating right writs by 30 deg around global x axis (left-hand side matrix multiplication for rotation only, position is constant)"
    synchronized_time = rospy.Time.now() + rospy.Duration(0.5)
    T_B_Tr = velma.getTf("B", "Tr")
    T_B_Trd = PyKDL.Frame( PyKDL.Rotation.RotX(30.0/180.0*math.pi) * T_B_Tr.M, T_B_Tr.p )
    T_B_Tl = velma.getTf("B", "Tl")
    T_B_Tld = PyKDL.Frame( PyKDL.Rotation.RotX(30.0/180.0*math.pi) * T_B_Tl.M, T_B_Tl.p )
    if not velma.moveCartImpRight([T_B_Trd, T_B_Tr], [2.0, 4.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if not velma.moveCartImpLeft([T_B_Tld, T_B_Tl], [2.0, 4.0], None, None, None, None, PyKDL.Wrench(PyKDL.Vector(5,5,5), PyKDL.Vector(5,5,5)), stamp=synchronized_time):
        exitError(8)
    if velma.waitForEffectorRight() != 0:
        exitError(9)
    if velma.waitForEffectorLeft() != 0:
        exitError(9)
    rospy.sleep(0.5)

    planAndExecute(q_map_starting)

    exitError(0)

    '''