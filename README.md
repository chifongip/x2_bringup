# X2 shared bringup

`state_publisher.launch.py` is the single owner of the X2 shared robot state.
It expands the canonical control description, starts the controller manager,
activates `joint_state_broadcaster`, and starts `robot_state_publisher`.

```bash
ros2 launch x2_bringup state_publisher.launch.py \
  command_transport:=zmq
```

It publishes the standard `/joint_states`, `/tf`, and `/tf_static` interfaces.
Start it once per robot. Navigation and MoveIt must consume these interfaces;
they must not start additional robot-state publishers or controller managers.

This launch does not activate the arm trajectory controller. The manipulation
or MoveIt launch owns `dual_arm_controller` when arm motion is required.

When the shared state launch is already running, start MoveIt or manipulation
with `start_state_bringup:=false` so it consumes the existing `/joint_states`
and TF topics instead of starting a second controller manager.

`initial_arm_command_mode` belongs to the hardware instance. Therefore, when
using `start_state_bringup:=false`, pass `initial_arm_command_mode:=zero` to
the original `state_publisher.launch.py` command; a later MoveIt or
manipulation launch cannot change it.

For applications that already own `/joint_states` and only need link TF, use
the passive launch:

```bash
ros2 launch x2_bringup rsp.launch.py
```

Unlike `state_publisher.launch.py`, the passive launch never starts hardware,
a controller manager, or a joint-state broadcaster.
