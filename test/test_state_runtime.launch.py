import time
import unittest
from pathlib import Path

import launch
import launch_testing.actions
import rclpy
from ament_index_python.packages import get_package_share_directory
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource


def generate_test_description():
    bringup_path = Path(get_package_share_directory("x2_bringup"))
    shared_state = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            str(bringup_path / "launch" / "state_publisher.launch.py")
        ),
        launch_arguments={"use_fake_hardware": "true"}.items(),
    )

    return launch.LaunchDescription(
        [shared_state, launch_testing.actions.ReadyToTest()]
    )


class TestSharedStateRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rclpy.init()

    @classmethod
    def tearDownClass(cls):
        rclpy.shutdown()

    def setUp(self):
        self.node = rclpy.create_node("test_shared_state_runtime")

    def tearDown(self):
        self.node.destroy_node()

    def wait_for(self, predicate, timeout=30.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            rclpy.spin_once(self.node, timeout_sec=0.1)
            if predicate():
                return
        self.fail("Timed out waiting for the shared state graph")

    def test_single_shared_state_pipeline(self):
        expected_nodes = {
            "controller_manager",
            "joint_state_broadcaster",
            "robot_state_publisher",
        }

        def pipeline_is_ready():
            names = [
                name for name, _ in self.node.get_node_names_and_namespaces()
            ]
            return expected_nodes.issubset(names)

        self.wait_for(pipeline_is_ready)

        names = [
            name for name, _ in self.node.get_node_names_and_namespaces()
        ]
        for name in expected_nodes:
            self.assertEqual(names.count(name), 1)

        def topics_are_ready():
            return (
                len(self.node.get_publishers_info_by_topic("/joint_states")) == 1
                and len(self.node.get_publishers_info_by_topic("/tf")) == 1
                and len(self.node.get_publishers_info_by_topic("/tf_static")) == 1
            )

        self.wait_for(topics_are_ready)
