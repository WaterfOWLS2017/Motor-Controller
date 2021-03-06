#!/usr/bin/env python
'''
 Node to interface motor controllers to ROS
 Looks for motor power and motor node number from ROS 
 Outputs the motor response information to ROS
'''
from motor_comm import *
import rospy
from motors.msg import MotorPower
from motors.msg import MotorResponse

import atexit

last_power_update_time = 0


def power_level(data,motors):
  '''
  Function to send power levels to motor 
  '''
  global last_power_update_time
  last_power_update_time = rospy.get_rostime().to_sec()

  motors.set_thrust(data.power1,data.power2)

def motor_response_to_ros(motors):
  '''
  Function to take motor response and put it on ROS
  '''
  motor_data = MotorResponse()

  #filling out MotorResponse message
  motor_data.header.stamp.secs = motors.now.secs
  motor_data.header.stamp.nsecs = motors.now.nsecs
  motor_data.motor_id = motors.response[1]
  motor_data.rpm = motors.response[7]
  motor_data.bus_voltage = motors.response[8]
  motor_data.bus_current = motors.response[9]
  motor_data.temperature = motors.response[10]
  motor_data.fault_flag = motors.response[11]
  motors.toggle_node_id()  

  motors.pub.publish(motor_data)    
  
  
def cleanup(motors):
  motors.set_thrust(0.0, 0.0)
  motors.send_motors_power_level()
  
def motor_node():
  '''
  Top level function to handle connection of motors with ROS
  '''
  motors = motor_comm()
  atexit.register(cleanup, motors=motors)
  global last_power_update_time

  motors.pub = rospy.Publisher('motor_data', MotorResponse, queue_size=10)
  rospy.init_node('motor_comm')
  rate = rospy.Rate(20)
  
  print "entering main loop"
  #spins at rate and puts the motors response on ROS
  while not rospy.is_shutdown():
    motors.now = rospy.get_rostime()

    if(motors.now.to_sec() - last_power_update_time) > 5:
      motors.set_thrust(0.0, 0.0)

    if motors.send_motors_power_level():
      motor_response_to_ros(motors)
    rospy.Subscriber("motor_power", MotorPower, power_level, motors)
    rate.sleep()

if __name__ == '__main__':
  print "starting main"
  try: 
    motor_node()
  except rospy.ROSInterruptException:
    pass
