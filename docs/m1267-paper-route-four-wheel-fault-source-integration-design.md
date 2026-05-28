# M1267 Paper-Route Four-Wheel Fault Source Integration Design

## Summary

M1267 designs how the M1266 four-wheel fault dynamics primitive should enter
source mining.

Decision:

```text
four_wheel_fault_source_integration_design_admit_source_shape_smoke
```

Admit next bounded implementation:

```text
m1268-paper-route-four-wheel-fault-source-shape-smoke
```

This is design-only. No training, PPO, checkpoint promotion, private holdout,
actor-input expansion, accepted-threshold relaxation, source-positive claim,
self-identification claim, paper-level claim, or high-fidelity validation claim
occurs in M1267.

## Integration Principle

Do not immediately integrate the four-wheel model into the main Gym training
environment.

First answer a simpler source question:

```text
Does the four-wheel fault model contain matched-current emergency states where
two hidden fault branches require different action sequences under the same
visible scene and ego state?
```

If the answer is still no, actor/history work remains blocked. If the answer is
yes, later milestones can integrate policy rollouts, recurrent hidden state,
and human-view observation compatibility.

## Source Snapshot Schema

Create a source-only snapshot type in the next implementation:

```text
FourWheelSourceSnapshot
```

Required fields:

```text
snapshot_id
scenario_id
seed
fault_name
fault_family
fault_severity
step
state
observation_72
info
obstacle_body_x
obstacle_body_y
obstacle_half_width
previous_action
```

Simulator-only metadata:

```text
fault_scales
per-wheel force summaries
per-wheel capacities
yaw_moment
```

The metadata may be written to artifacts, but must not enter the actor
observation.

## Human-View Observation Mapping

The next smoke should produce a 72-value human-view-compatible observation,
even if no actor consumes it yet.

Required visible fields:

```text
vx
vy
yaw_rate
ax-like response from previous model step
ay-like response from previous model step
steer actuator state
steer rate
throttle actuator state
brake actuator state
previous steer command
previous throttle command
previous brake command
road/free-space geometry in ego frame
obstacle geometry in ego frame
```

Forbidden fields:

```text
fault label
per-wheel mu
per-wheel brake/drive scale
per-wheel tire force
slip ratio
oracle feasibility
candidate id
search result
success/collision/progress labels
```

For M1268, road/free-space can be a simple straight corridor and obstacle
geometry can be a compact ego-frame obstacle representation. The purpose is
source shape, not final perception fidelity.

## Source-Shape Smoke

M1268 should be no-policy and no-training.

It should generate matched-current hidden-fault pairs by holding visible state
and obstacle geometry fixed while varying only simulator-internal fault scales.

Initial fault families:

```text
left_right_split_mu
single_wheel_brake_pull
single_wheel_grip_collapse
halfshaft_torque_loss
```

Important timing condition:

```text
Include source states with established brake or drive actuator force.
```

M1266 showed that split-mu yaw response appears when brake pressure has reached
the asymmetric tire boundary. A source collector that only samples the first
actuator-lag step can miss the fault effect.

## Candidate Actions

Use short open-loop action sequences first:

```text
hold brake
release brake
left steer + brake
right steer + brake
left steer + throttle release
right steer + throttle release
steer reversal
```

The output remains the same control contract:

```text
steer / throttle / brake
```

No per-wheel control is introduced.

## Rollout Evaluation

Each candidate sequence should be rolled out under both hidden branches:

```text
condition A with candidate A
condition A with candidate B
condition B with candidate B
condition B with candidate A
```

Compute obstacle clearance and strict source acceptance:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
best_action_l2 >= 0.12
cross_regret_A >= 0.02
cross_regret_B >= 0.02
```

Do not lower thresholds.

## Expected Artifacts

M1268 should write:

```text
runs/m1268_four_wheel_fault_source_shape_smoke/summary.json
runs/m1268_four_wheel_fault_source_shape_smoke/scenario_summary.csv
runs/m1268_four_wheel_fault_source_shape_smoke/snapshot_candidates.csv
runs/m1268_four_wheel_fault_source_shape_smoke/action_lattice.csv
runs/m1268_four_wheel_fault_source_shape_smoke/action_rollouts.csv
runs/m1268_four_wheel_fault_source_shape_smoke/matched_capability_pairs.csv
runs/m1268_four_wheel_fault_source_shape_smoke/accepted_separable_pairs.csv
runs/m1268_four_wheel_fault_source_shape_smoke/rejected_pairs.csv
runs/m1268_four_wheel_fault_source_shape_smoke/model_fidelity_limits.md
```

Required summary guardrails:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
accepted_thresholds_relaxed: false
source_positive: true/false
```

## Comparison Baseline

M1268 should compare source shape against current branch evidence:

```text
M1259 accepted_separable_pairs: 0
M1259 best_actions_diverged_pairs: 4
M1262 accepted_separable_pairs: 0
M1262 max min_cross_regret: 0.0043813964
```

M1268 does not need to beat policy performance. It needs to answer whether the
new dynamics source contains separable source rows at all.

## Stop Conditions

Stop before implementation if any of these become necessary:

```text
actor input must include per-wheel/fault labels
accepted-source thresholds must be lowered
source reconstruction cannot be deterministic
the smoke requires PPO/training
```

Stop after M1268 and audit before continuing if:

```text
accepted_separable_pairs == 0
all accepted-looking rows are collision-dominated
source-positive rows all come from one seed/fault pair only
observation mapping accidentally includes forbidden metadata
```

## Next Step

Admit:

```text
m1268-paper-route-four-wheel-fault-source-shape-smoke
```

The next milestone should implement the no-policy source-shape smoke, not train
or promote a driver.
