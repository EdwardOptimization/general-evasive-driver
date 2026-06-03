# Actor Contract

P0 observation shape: 72

action shape: 3

actor encoder: `human_view_online_gru`

action sequence horizon: `1`

Action vector:

```text
[steering_command, throttle_command, brake_command]
```

Physical pedal mapping:

```text
physical_throttle = 0.5 * (throttle_command + 1)
physical_brake = 0.5 * (brake_command + 1)
```

Allowed actor-visible inputs:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent state from past command-response history
```

Forbidden actor-visible inputs:

```text
mu mass tire stiffness brake scale actuator tau slip tire force oracle
feasibility AEB/AES/drift labels controller mode speed_ref beta_target
path error heading error path curvature TTC required clearance oracle stopping
distance reward terms success labels
```
