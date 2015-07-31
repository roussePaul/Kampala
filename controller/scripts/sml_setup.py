#Vinzenz Minnig, 2015
#Contains the necessary function for the system setup while working with mavros and the qualysis motion capture system

import rospy
from mavros.srv import ParamSet, ParamGet
from mavros.srv import CommandBool
from mavros.srv import SetMode
from mocap.srv import BodyData
import sys

import analysis
import utils

## Set the flight mode of the quad.
##
## @param MODE: select the flight mode (MANUAL CIRCLE STABILIZE FLY_BY_WIRE_A FLY_BY_WIRE_B AUTO RTL LOITER GUIDED INITIALISING)
def Set_Flight_Mode(MODE):
	return_value=True

	#Change the flight mode on the Pixhawk flight controller
	try:
		rospy.wait_for_service('mavros/set_mode',10)
	except:
		utils.logerr('Mavros is not available')
		return_value=False

	utils.loginfo('Changing flight mode to '+MODE+' ...')

	rospy.sleep(2)

	try:
		change_param=rospy.ServiceProxy('mavros/set_mode',SetMode)
		param=change_param(0,MODE)
		while param.success==False:
			param=change_param(0,MODE)
			if param.success==False:
				utils.logerr('Cannot change flight mode')
		if param.success:
			utils.loginfo('Flight mode changed to '+MODE)
		else:
			utils.logerr('Cannot change flight mode')
			return_value=False
	except:
		utils.logerr('Cannot change flight mode')
		return_value=False


	return return_value

## Set the system ID.
##
## This is necessary to set the SYSID_MYGCS parameter before flying.
##
## @param id_int: value of the SYSID_MYGCS parameter
def Set_System_ID(id_int):
	return_value=True

	#Necesary to allow RCOverride
	#Also checks if there is a connection to Mavros, and shuts down if there isn't

	utils.loginfo('Connecting to Mavros ...')
	try:
		rospy.wait_for_service('mavros/param/set',10)
	except:
		utils.logerr('Mavros is not available (fail to contact service mavros/param/set).')
		return_value=False
	utils.loginfo('Connected to Mavros')

	utils.loginfo('Changing system ID ...')

	rospy.sleep(2)

	try:
		change_param=rospy.ServiceProxy('mavros/param/set',ParamSet)
		param=change_param('SYSID_MYGCS',id_int,0.0)

		if param.success:
			utils.loginfo('System ID changed')
		else:
			utils.logerr('Cannot change system ID')
			return_value=False
	except:
		utils.logerr('Cannot change system ID')
		return_value=False


	return return_value

## Force the SYSID_MYGCS parameter set
## This function loop as long as the parameter SYSID_MYGCS is not successfully set
## @param id_int: value of the SYSID_MYGCS parameter
def Wait_For_ID(id_int):
	return_value=False

	# Wait for Mavros connection and wait until the parameter SYSID_MYGCS is available

	utils.loginfo('Connecting to Mavros ...')
	try:
		rospy.wait_for_service('mavros/param/set',10)
	except:
		utils.logerr('Mavros is not available (fail to contact service mavros/param/set).')
		return_value=False
	utils.loginfo('Connected to Mavros')

	set_param=rospy.ServiceProxy('mavros/param/set',ParamSet)
	while return_value==False:
		try:
			param=set_param('SYSID_MYGCS',id_int,0.0)
			if param.success:
				utils.loginfo('System ID changed')
				return_value=True
			else:
				utils.logerr('Cannot change system ID')
				return_value=False
		except:
			utils.logerr('Cannot connect to the service "mavros/param/set" to change system ID')
			return_value=False
		rospy.sleep(5)

	utils.loginfo('Iris initialised...')
	return return_value

## Force the arming.
##
## This function ask for the quad arm as long as this is not successful
def Wait_For_Arming():
	return_value=False

	#Arming the Quad
	try:
		utils.loginfo('Arming Quad ...')
		rospy.wait_for_service('mavros/cmd/arming',10)
	except:
		utils.logerr('No connection to Mavros')
		return_value=False

	try:
		arming=rospy.ServiceProxy('mavros/cmd/arming',CommandBool)
		arming_result=arming(True)
	except:
		utils.logerr('Cannot arm quad')
		return_value=False

	rospy.sleep(1)


	set_param=rospy.ServiceProxy('mavros/param/set',ParamSet)
	while return_value==False:
		#Arming has to be done twice sometimes...
		try:
			arming=rospy.ServiceProxy('mavros/cmd/arming',CommandBool)
			arming_result=arming(True)
			if arming_result.success:
				utils.loginfo('Quad is now armed')
			else:
				utils.logerr('Cannot arm quad')
				return_value=False
		except:
			utils.logerr('Cannot arm quad')
			return_value=False
		rospy.sleep(20)


	return return_value


## Wait until the mocap node is up and that the services are available
def Connect_To_Mocap():
	#Connect to the Motion Capture System, flag an error if it is unavailable

	try:
		utils.loginfo('Connecting to the mocap system...')
		rospy.wait_for_service('mocap_get_data',10)
	except:
		utils.logerr('No connection to the mocap system')
		sys.exit()
	utils.loginfo('Connected to Mocap')

	return rospy.ServiceProxy('mocap_get_data',BodyData)

## Arm the quad.
##
## This function ask for the quad arming.
##
## @param basename: name of the iris group (iris1, iris2, ...)
def Arming_Quad(base_name=""):
	return_value=True

	#Arming the Quad
	srv_path = 'mavros/cmd/arming'
	if base_name!="":
		srv_path = "/%s/%s"%(base_name,srv_path)

	try:
		utils.loginfo('Arming Quad ...')
		rospy.wait_for_service(srv_path,10)
	except:
		utils.logerr('No connection to Mavros')
		return_value=False

	try:
		arming=rospy.ServiceProxy(srv_path,CommandBool)
		arming_result=arming(True)
	except:
		utils.logerr('Cannot arm quad')
		
		return_value=False

	rospy.sleep(1)

	#Arming has to be done twice sometimes...
	try:
		arming=rospy.ServiceProxy(srv_path,CommandBool)
		arming_result=arming(True)
	except:
		utils.logerr('Cannot arm quad')
		return_value=False

	rospy.sleep(1)

	if arming_result.success:
		utils.loginfo('Quad is now armed')
	else:
		utils.logerr('Cannot arm quad')
		return_value=False

	return return_value

