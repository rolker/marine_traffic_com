cmake_minimum_required(VERSION 2.8.3)
project(marine_traffic_com)

## Compile as C++11, supported in ROS Kinetic and newer
add_compile_options(-std=c++11)

find_package(catkin REQUIRED COMPONENTS
  geographic_msgs
  project11_msgs
  rospy
  dynamic_reconfigure
  project11
)

catkin_python_setup()

generate_dynamic_reconfigure_options(
    cfg/marine_traffic_com.cfg
)

catkin_package(
#  INCLUDE_DIRS include
#  LIBRARIES posmv
#  CATKIN_DEPENDS geometry_msgs project11_msgs rospy
#  DEPENDS system_lib
)

