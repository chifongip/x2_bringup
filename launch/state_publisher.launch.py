from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context):
    command_transport = LaunchConfiguration("command_transport")
    zmq_endpoint = LaunchConfiguration("zmq_endpoint")
    leg_state_topic = LaunchConfiguration("leg_state_topic")
    waist_state_topic = LaunchConfiguration("waist_state_topic")
    arm_state_topic = LaunchConfiguration("arm_state_topic")
    head_state_topic = LaunchConfiguration("head_state_topic")
    gains_file = LaunchConfiguration("ros2_control_gains_file")
    control_update_rate = LaunchConfiguration("ros2_control_update_rate")
    use_fake_hardware = LaunchConfiguration("use_fake_hardware")
    package_path = Path(get_package_share_directory("x2_bringup"))

    robot_description = {
        "robot_description": ParameterValue(
            Command(
                [
                    "xacro ",
                    str(package_path / "config" / "x2_ultra.urdf.xacro"),
                    " use_fake_hardware:=",
                    use_fake_hardware,
                    " command_transport:=",
                    command_transport,
                    " zmq_endpoint:=",
                    zmq_endpoint,
                    " leg_state_topic:=",
                    leg_state_topic,
                    " waist_state_topic:=",
                    waist_state_topic,
                    " arm_state_topic:=",
                    arm_state_topic,
                    " head_state_topic:=",
                    head_state_topic,
                    " ros2_control_gains_file:=",
                    gains_file,
                ]
            ),
            value_type=str,
        )
    }

    return [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            output="screen",
            parameters=[robot_description, {"publish_frequency": 50.0}],
        ),
        Node(
            package="controller_manager",
            executable="ros2_control_node",
            output="screen",
            parameters=[
                robot_description,
                str(package_path / "config" / "ros2_controllers.yaml"),
                {
                    "update_rate": ParameterValue(
                        control_update_rate, value_type=int
                    )
                },
            ],
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=[
                "joint_state_broadcaster",
                "--controller-manager",
                "/controller_manager",
            ],
            output="screen",
        ),
    ]


def generate_launch_description():
    package_path = Path(get_package_share_directory("x2_bringup"))
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "use_fake_hardware",
                default_value="false",
                choices=["true", "false"],
                description="Use ros2_control mock hardware instead of X2 HAL state streams.",
            ),
            DeclareLaunchArgument(
                "command_transport",
                default_value="ros_topic",
                choices=["ros_topic", "zmq"],
                description="Exclusive X2 arm command transport.",
            ),
            DeclareLaunchArgument(
                "zmq_endpoint",
                default_value="tcp://*:8559",
                description="ZMQ PUB endpoint used when command_transport is zmq.",
            ),
            DeclareLaunchArgument(
                "leg_state_topic", default_value="/aima/hal/joint/leg/state"
            ),
            DeclareLaunchArgument(
                "waist_state_topic", default_value="/aima/hal/joint/waist/state"
            ),
            DeclareLaunchArgument(
                "arm_state_topic", default_value="/aima/hal/joint/arm/state"
            ),
            DeclareLaunchArgument(
                "head_state_topic", default_value="/aima/hal/joint/head/state"
            ),
            DeclareLaunchArgument(
                "ros2_control_gains_file",
                default_value=str(
                    package_path / "config" / "x2_ros2_control_gains.yaml"
                ),
                description="YAML file containing per-arm-joint stiffness and damping.",
            ),
            DeclareLaunchArgument(
                "ros2_control_update_rate",
                default_value="100",
                description=(
                    "Controller-manager loop rate in Hz. The 100 Hz default leaves "
                    "headroom for safety-critical HAL state delivery."
                ),
            ),
            OpaqueFunction(function=launch_setup),
        ]
    )
