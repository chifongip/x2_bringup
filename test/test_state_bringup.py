import importlib.util
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

from launch import LaunchContext


PACKAGE_DIR = Path(__file__).parents[1]
CONFIG_DIR = PACKAGE_DIR / "config"
LAUNCH_FILE = PACKAGE_DIR / "launch" / "state_publisher.launch.py"
RSP_LAUNCH_FILE = PACKAGE_DIR / "launch" / "rsp.launch.py"
XACRO = CONFIG_DIR / "x2_ultra.urdf.xacro"


def load_launch_module():
    spec = importlib.util.spec_from_file_location("state_publisher_launch", LAUNCH_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expand(**mappings):
    command = ["xacro", str(XACRO)]
    command.extend(f"{name}:={value}" for name, value in mappings.items())
    return ET.fromstring(subprocess.check_output(command, text=True))


def test_launch_description_constructs():
    assert load_launch_module().generate_launch_description().entities


def test_passive_rsp_launch_does_not_start_hardware():
    source = RSP_LAUNCH_FILE.read_text(encoding="utf-8")

    assert 'package="robot_state_publisher"' in source
    assert "ros2_control_node" not in source
    assert "spawner" not in source


def test_state_launch_owns_only_shared_state_nodes():
    context = LaunchContext()
    context.launch_configurations.update(
        {
            "use_fake_hardware": "false",
            "command_transport": "zmq",
            "initial_arm_command_mode": "zero",
            "zmq_endpoint": "tcp://*:8559",
            "leg_state_topic": "/aima/hal/joint/leg/state",
            "waist_state_topic": "/aima/hal/joint/waist/state",
            "arm_state_topic": "/x2_test/aima/hal/joint/arm/state",
            "head_state_topic": "/aima/hal/joint/head/state",
            "ros2_control_gains_file": str(
                CONFIG_DIR / "x2_ros2_control_gains.yaml"
            ),
            "ros2_control_update_rate": "100",
        }
    )

    nodes = load_launch_module().launch_setup(context)
    assert len(nodes) == 3
    source = LAUNCH_FILE.read_text(encoding="utf-8")
    assert 'package="robot_state_publisher"' in source
    assert 'executable="ros2_control_node"' in source
    assert '"joint_state_broadcaster"' in source
    assert '"dual_arm_controller"' not in source


def test_real_control_description_has_31_states_and_14_arm_commands():
    root = expand(use_fake_hardware="false", command_transport="ros_topic")
    control = root.find("ros2_control")
    assert control is not None
    assert control.findtext("hardware/plugin") == "agibot_x2_ros2_control/X2SystemHardware"
    joints = control.findall("joint")
    assert len(joints) == 31
    assert all(
        {item.get("name") for item in joint.findall("state_interface")}
        == {"position", "velocity", "effort"}
        for joint in joints
    )
    commanded = [joint for joint in joints if joint.findall("command_interface")]
    assert len(commanded) == 14
    assert all(
        joint.find("command_interface").get("name") == "position"
        for joint in commanded
    )


def test_fake_default_and_locomanipulation_gains():
    root = expand()
    control = root.find("ros2_control")
    assert control.findtext("hardware/plugin") == "mock_components/GenericSystem"
    joints = {joint.get("name"): joint for joint in control.findall("joint")}
    shoulder_parameters = {
        item.get("name"): float(item.text)
        for item in joints["left_shoulder_pitch_joint"].findall("param")
    }
    wrist_parameters = {
        item.get("name"): float(item.text)
        for item in joints["right_wrist_roll_joint"].findall("param")
    }
    assert shoulder_parameters == {"stiffness": 50.0, "damping": 3.0}
    assert wrist_parameters == {"stiffness": 20.0, "damping": 2.0}


def test_hardware_topic_overrides_are_preserved():
    root = expand(
        use_fake_hardware="false",
        command_transport="zmq",
        initial_arm_command_mode="zero",
        arm_state_topic="/x2_test/aima/hal/joint/arm/state",
    )
    parameters = {
        item.get("name"): item.text
        for item in root.findall("ros2_control/hardware/param")
    }
    assert parameters["command_transport"] == "zmq"
    assert parameters["initial_arm_command_mode"] == "zero"
    assert parameters["zmq_endpoint"] == "tcp://*:8559"
    assert parameters["leg_state_topic"] == "/aima/hal/joint/leg/state"
    assert parameters["waist_state_topic"] == "/aima/hal/joint/waist/state"
    assert parameters["arm_state_topic"] == "/x2_test/aima/hal/joint/arm/state"
    assert parameters["head_state_topic"] == "/aima/hal/joint/head/state"


def test_controller_configuration_preserves_state_delivery_headroom():
    with (CONFIG_DIR / "ros2_controllers.yaml").open(encoding="utf-8") as stream:
        config = yaml.safe_load(stream)

    manager = config["controller_manager"]["ros__parameters"]
    controller = config["dual_arm_controller"]["ros__parameters"]
    constraints = controller["constraints"]
    assert manager["update_rate"] == 100
    assert controller["allow_nonzero_velocity_at_trajectory_end"] is False
    assert constraints["goal_time"] > 0.0
    assert constraints["stopped_velocity_tolerance"] > 0.0
    assert set(controller["joints"]) == {
        name
        for name, values in constraints.items()
        if isinstance(values, dict) and "goal" in values
    }
    assert all(constraints[joint]["goal"] > 0.0 for joint in controller["joints"])
