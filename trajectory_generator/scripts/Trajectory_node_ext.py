#!/usr/bin/env python
import rospy
from Trajectory_node import TrajectoryNode
from mocap.msg import QuadPositionDerivedExt
from controller.msg import Permission

class TrajectoryNodeExt(TrajectoryNode):

  def __init__(self,group=''):
    rospy.init_node('TG')
    abspath = ""
    if group:
    	abspath = "/"+group
    self.pub = rospy.Publisher(abspath+'trajectory_gen/target_ext',QuadPositionDerivedExt, queue_size=10)
    self.security_pub = rospy.Publisher(abspath+'trajectory_gen/done', Permission, queue_size=10)
