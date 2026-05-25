# M810 V4 Low-Margin New Data Route Design

## Purpose

M810 designs the next no-training data route after M809 closed the
`v4_low_margin_source_diverse_corpus_refresh` branch.

The question is:

```text
How should we generate source-diverse near-boundary normal rows without
continuing to overfit M801/M804 public geometry anchors?
```

This milestone is design-only:

```text
no implementation
no replay
no residual calibration
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Branch Change

The previous branch tried to populate the strict primary band by broad source
refresh and post-hoc retargeting:

```text
M801: broad source refresh found no primary successful rows
M804: boundary-window retarget found primary rows only via half-width geometry
M807: multi-axis expansion still accepted only half-width geometry
```

M810 changes the search problem:

```text
from:
  retarget fixed public anchors after the fact

to:
  generate near-boundary source states during scenario collection by jointly
  varying warm-up history, fault timing, obstacle timing, and obstacle geometry
```

The goal is not more random data. The goal is source-diverse data with the
right causal structure:

```text
history and current response should matter before the emergency decision,
not only obstacle half-width after replay.
```

## Actor Contract

The actor remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

No deploy-time input may include:

```text
mu
mass / tire / brake / actuator hidden parameters
slip ratio
tire force
friction margin
oracle feasibility labels
TTC
required clearance
reference trajectory
success or collision labels
```

Training-time and corpus-mining tools may use simulator metadata for logging,
balancing, and offline diagnostics only.

## Current Simulator Limits

The current backend is still a single-track model with current-model proxy
faults. M810 must keep this language precise:

```text
allowed claim:
  current-model or current-model-proxy capability faults

forbidden claim:
  physically faithful single-wheel blowout, split-mu, halfshaft, stuck-caliper,
  suspension, or wheel-speed effects
```

Those true wheel-level failures require a future four-wheel or higher-fidelity
backend. The current route can still be useful for self-identification research
because it varies closed-loop capability envelopes, but it must not overclaim
fidelity.

## Proposed Data Route

M811 should implement a no-training corpus generator with five stages.

### Stage 1: Active Diagnostic Warm-Up

Before the obstacle-critical phase, collect short warm-up segments under the
same frozen actor and hidden state.

Warm-up modes:

```text
natural_policy:
  no perturbation, baseline on-policy history

steer_pulse_left_right:
  small bounded steering perturbation before the obstacle is near

brake_tap:
  small bounded brake perturbation before the obstacle is near

combined_micro_probe:
  small steer and brake perturbation with strict safety bounds
```

These are data-generation probes, not deploy-time rules. The actor contract
does not change; the generated hidden state simply contains a richer
command-response history before the emergency.

Safety limits:

```text
probe duration <= 0.4 s
steer perturbation <= 0.08 normalized action
brake perturbation <= 0.08 normalized action
discard if warm-up causes collision, off-road, spin, or obstacle proximity risk
```

### Stage 2: Joint Fault And Obstacle Timing

Instead of changing only obstacle width after a fixed snapshot, jointly sample:

```text
fault family
fault severity
fault activation step
obstacle longitudinal spawn / timing
obstacle lateral offset
obstacle half-width
road curvature family
initial speed band
warm-up mode
```

The sampler should deliberately seek a normal-history result near the strict
primary band:

```text
0.0 <= normal min_clearance_margin <= 0.00005
```

But it should also keep collision-edge and diagnostic-safe rows for bracketing:

```text
collision_edge: -0.001 <= margin < 0
safe_edge: 0 < margin <= 0.01
diagnostic_safe: 0.01 < margin <= 0.2
```

### Stage 3: In-Collection Boundary Search

Boundary search should happen while generating scenarios, not only after a
public row exists.

For each seed/fault/warm-up group, M811 should bracket over:

```text
obstacle appearance step or longitudinal spawn
obstacle lateral offset
obstacle half-width
fault activation step
fault severity scale
```

The active unit is a source group:

```text
seed + preferred fault + warm-up mode + obstacle timing family
```

M811 should keep at most a small number of rows per source group. This prevents
one group from filling the corpus through width-only bisection.

### Stage 4: History Interventions

For accepted primary rows, replay paired interventions:

```text
normal
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
delayed_history
scaled_response_history
wrong_history_from_matched_fault
```

The current M807 route found half-width rows where local intervention branches
still collide, but the rows were not source-diverse. M811 should preserve the
history-intervention evidence while fixing source diversity.

### Stage 5: Source-Balanced Export

M811 should export a source-balanced corpus before any calibration is allowed.

Primary pass requires:

```text
accepted primary rows >= 80
unique seeds >= 8
unique source groups >= 16
unique source indices >= 8
unique fault-family pairs >= 4
unique warm-up modes >= 2
unique boundary axes >= 3
max seed dominance <= 0.25
max source-group dominance <= 0.15
max fault-family-pair dominance <= 0.40
max boundary-axis dominance <= 0.60
normal collision rate in accepted rows == 0.0
actor checksum unchanged
residual-head checksum unchanged
training_started == false
optimizer_started == false
ppo_used == false
promoted == false
```

At least `10` accepted rows should come from at least `3` boundary axes.

## Boundary Axes

M811 should distinguish how a row entered the primary band:

```text
obstacle_timing
obstacle_lateral_offset
obstacle_half_width
fault_activation_step
fault_severity
warmup_probe_mode
road_curvature_or_speed
```

This is not an actor input. It is offline provenance for corpus balance.

## Outputs

M811 should write:

```text
runs/m811_v4_low_margin_new_data_route/source_group_rows.csv
runs/m811_v4_low_margin_new_data_route/warmup_probe_rows.csv
runs/m811_v4_low_margin_new_data_route/boundary_search_plan_rows.csv
runs/m811_v4_low_margin_new_data_route/boundary_search_replay_rows.csv
runs/m811_v4_low_margin_new_data_route/accepted_primary_rows.csv
runs/m811_v4_low_margin_new_data_route/intervention_replay_rows.csv
runs/m811_v4_low_margin_new_data_route/source_balance_summary.csv
runs/m811_v4_low_margin_new_data_route/axis_balance_summary.csv
runs/m811_v4_low_margin_new_data_route/fault_proxy_limitations.md
runs/m811_v4_low_margin_new_data_route/progress.jsonl
runs/m811_v4_low_margin_new_data_route/summary.json
docs/m811-v4-low-margin-new-data-route-implementation.md
```

Each accepted row should include:

```text
source_group_id
seed
source_index
warmup_mode
preferred_fault
preferred_fault_family
wrong_fault
wrong_fault_family
fault_family_pair
boundary_axis
obstacle_timing_delta
obstacle_lateral_delta
obstacle_half_width_delta
fault_activation_step_delta
fault_severity_delta
road_curvature_bucket
initial_speed_bucket
normal_margin
normal_success
normal_collision
intervention_success
intervention_collision
intervention_margin
```

## Result Classes

M811 should classify results explicitly:

```text
v4_low_margin_new_data_route_pass
v4_low_margin_new_data_route_sparse
v4_low_margin_new_data_route_source_concentrated
v4_low_margin_new_data_route_axis_concentrated
v4_low_margin_new_data_route_warmup_probe_artifact
v4_low_margin_new_data_route_proxy_limit
v4_low_margin_new_data_route_replay_error
v4_low_margin_new_data_route_contract_violation
```

Only `v4_low_margin_new_data_route_pass` may admit a new active-steer guard
calibration design. Any other result requires an audit.

## M811 Implementation Constraints

M811 must not:

```text
train actor or residual parameters
train a calibrator
run PPO
promote a checkpoint
weaken the primary 0.00005 margin threshold
count collision rows as accepted successes
use private holdout feedback
add oracle deploy-time inputs
claim true wheel-level faults from current single-track proxy data
accept M804/M807 half-width-only rows as pass evidence
```

M811 may reuse M804/M807 half-width rows only as:

```text
debug reference rows
negative examples for source/axis concentration
tool regression checks
```

## Supported Design Claim

M810 supports only this claim:

```text
After M809, the highest-leverage next step is a new no-training data route
that generates source-diverse near-boundary rows during scenario collection,
not another fixed-anchor retarget-axis tweak.
```

It does not claim that M811 will pass or that the driver improved.

## Next Blocker

```text
m811-v4-low-margin-new-data-route-implementation
```
