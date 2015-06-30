#!/usr/bin/env python
import rospy
import sys
import ast
import math
import numpy
from mocap.msg import QuadPositionDerived
from trajectory_generato import TrajectoryGenerator
from trajectory import Trajectory
from Trajectory_node import TrajectoryNode
from straight_line_class import StraightLineGen
from circle_acc import AccGen
from potential import PotGen

#This script generates the points, velocities and accelerations to be used as a reference for the 
#controller to to get the quad to move in a circle.
#Given a midpoint, radius and speed a circle is generated such that the quad moves at a constant speed.
#Constraints on maximum velocity and acceleration are used.
#Everyhthing is calculated in a coordinatesystem that is rotated by an angle of theta about the z-axis of the SML-frame. The method transform_coordinates transforms a vector given in the rotated frame into the corresponding vector in the SML-frame. 

class VRT(Trajectory):
  
  done = False
  a_max = 0.6**2.0/0.8
  
  def __init__(self,trajectory_node,mid,start,velo,psi,my_id):
    Trajectory.__init__(self,trajectory_node)
    self.my_state = QuadPositionDerived()
    self.my_id = my_id
    self.tg = TrajectoryGenerator()
    self.midpoint = mid
    self.start = start
    n = [self.start[0]-self.midpoint[0],self.start[1]-self.midpoint[1],self.start[0]-self.midpoint[2]]
    self.radius = self.tg.get_distance(self.start,self.midpoint)
    self.initial_velo = velo
    self.velo = self.tg.get_norm(self.initial_velo)
    #define new coordinates
    self.e_n = self.tg.get_direction(n)
    self.yp = self.tg.get_direction(self.initial_velo)
    self.zp = numpy.cross(self.e_n,self.yp)
    self.psi = psi #angle of rotation about initial e_n direction
    self.w = self.radius*self.velo
    self.theta_z = self.tg.get_projection([0,0,1],self.e_n)
    rospy.Subscriber("/body_data/id_"+str(self.my_id),QuadPositionDerived, self.setMyState)
  
  def begin(self):
    v_max = (self.radius*self.a_max)**(0.5)
    if self.velo > v_max:
      self.velo = v_max
    self.__set_done(False)
    

  def loop(self, start_time):
    time = start_time
    r = 20.0
    rate = rospy.Rate(r)
    pg = PotGen()
    outvelo = [0.,0.5,0.]  #change
    outpos = [0.8,0.,0.6] #change
    while not rospy.is_shutdown() and not self.is_done():
      leader_pos = self.tg.get_circle_point(self.radius,self.w*time)
      leader_pos = self.tg.offset(outpos,self.midpoint)
      my_pos = self.__get_my_pos()
      e_r = self.tg.get_direction2(my_pos, leader_pos)
      print(e_r)
      dist = self.tg.get_distance(leader_pos, my_pos)
      outacc = pg.get_acceleration(dist, e_r)
      outvelo = pg.get_velocity(outvelo,outacc,1/r)
      outpos = pg.get_position(outpos, outvelo, 1/r)
      outpos.append(self.tg.adjust_yaw([1,0,0]))
      outvelo.append(0)
      outacc.append(0)
      outmsg = self.tg.get_message(outpos,outvelo,outacc)
      self.trajectory_node.send_msg(outmsg)
      self.trajectory_node.send_permission(False)
      rate.sleep()
      time += 1/r
      if self.w*time >= self.psi:
        leader_pos = self.tg.get_circle_point(self.radius,self.psi)
        leader_pos = self.tg.offset(outpos,self.midpoint)
        my_pos = self.__get_my_pos()
        e_r = self.tg.get_direction2(my_pos, leader_pos)
        dist = self.tg.get_distance(leader_pos, my_pos)
        outacc = pg.get_acceleration(dist, e_r)
        outvelo = pg.get_velocity(outvelo,outacc,time)
        outpos = pg.get_position(outpos, outvelo, time)
        outpos.append(self.tg.adjust_yaw([1,0,0]))
        outvelo.append(0)
        outacc.append(0)
        outmsg = self.tg.get_message(outpos,outvelo,outacc)
        self.trajectory_node.send_msg(outmsg)
        self.trajectory_node.send_permission(False)
        rate.sleep()
        time += 1/r
        self.__set_done(True)

    
  def is_done(self):
    return self.done

  def __set_done(self,boolean):
    self.done = boolean
   
  def setMyState(self, data):
    self.my_state = data  

  def __get_my_pos(self):
    return [self.my_state.x,self.my_state.y,self.my_state.z]

if __name__ == '__main__':
  try:
    vrt = VRT(TrajectoryNode(),[0.,0.,0.6],[0.8,0.0,0.6],[0.,0.5,0.], 2*math.pi, 8).loop(0.)
  except rospy.ROSInterruptException:
    pass
  
