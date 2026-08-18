cmake_minimum_required(VERSION 3.22)
project(x2_bringup)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(launch_testing_ament_cmake REQUIRED)
  ament_add_pytest_test(test_state_bringup test/test_state_bringup.py)
  add_launch_test(test/test_state_runtime.launch.py TIMEOUT 60)
endif()

install(DIRECTORY config launch DESTINATION share/${PROJECT_NAME})
install(FILES README.md DESTINATION share/${PROJECT_NAME})

ament_package()
