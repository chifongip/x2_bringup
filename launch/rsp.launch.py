from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    package_path = Path(get_package_share_directory("x2_bringup"))
    robot_description = {
        "robot_description": ParameterValue(
            Command(
                [
                    "xacro ",
                    str(package_path / "config" / "x2_ultra.urdf.xacro"),
                ]
            ),
            value_type=str,
        )
    }

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "publish_frequency",
                default_value="50.0",
                description="Maximum dynamic TF publication rate in Hz.",
            ),
            Node(
                package="robot_state_publisher",
                executable="robot_state_publisher",
                output="screen",
                parameters=[
                    robot_description,
                    {
                        "publish_frequency": ParameterValue(
                            LaunchConfiguration("publish_frequency"),
                            value_type=float,
                        )
                    },
                ],
            ),
        ]
    )
