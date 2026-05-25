# M824 V4 Extreme Hidden-Dynamics Data Route Design

## Purpose

M824 designs the next no-training data route after M823 rejected same-corpus
fixed-gate calibration.

The design question is:

```text
Can a broader extreme hidden-dynamics route produce source-diverse evidence
that command-response history matters, rather than more residual-gate tuning?
```

M824 is design-only:

```text
no implementation
no replay
no actor update
no residual-head update
no calibrator training
no PPO
no checkpoint promotion
```

## Motivation

M821/M822 showed that fixed residual suppression is not the missing control
variable on the M814/M817 corpus:

```text
identity ranked first
non-identity fixed gates had negative p05 margin lift
actor and M761 residual-head checksums stayed unchanged
PPO and promotion remained blocked
```

The next useful evidence must therefore come from data coverage and
history-intervention sensitivity:

```text
same apparent emergency geometry;
different hidden vehicle capability;
different correct action or margin outcome;
wrong/reset/delayed command-response history degrades behavior.
```

## Claim Boundary

The current simulator is still a single-track model with parameterized
capability changes. It can represent:

```text
global_mu_drop
front_lateral_authority_drop
rear_lateral_authority_drop
brake_authority_drop
drive_authority_drop
steering_fault
mass_cg_shift
delay_noise_fault
combined_fault
```

It can only proxy these real-world faults:

```text
single-wheel blowout
single-corner grip collapse
left/right split-mu
stuck single caliper
single-wheel brake pressure loss
halfshaft or CV torque asymmetry
corner suspension damage
wheel-speed sensor faults
```

M825 must mark each row with:

```text
fidelity_class = current_model_fault | current_model_proxy | future_only
```

and must not claim true wheel-level physical fidelity from current proxy rows.

## Data Route

M825 should build a no-training source-mining route using the M568 actor and
M761 residual head as the current behavior generator.

Frozen:

```text
M568 actor
M761 residual head
actor observation contract
alpha = 0.2 unless explicitly logged as a fixed replay parameter
```

No deploy-time actor input may include:

```text
fault labels
mu or tire parameters
oracle feasibility labels
TTC or required clearance
controller mode
success/collision labels
```

The route should reuse the current v4 fault distribution as the starting
coverage map:

```text
configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
```

but may emit a derived M825 route config if implementation needs smaller
runtime limits.

## Source Generation

M825 should generate source snapshots across:

```text
fault families:
  global_mu_drop
  front_lateral_authority_drop
  rear_lateral_authority_drop
  brake_authority_drop
  drive_authority_drop
  steering_fault
  mass_cg_shift
  delay_noise_fault
  combined_fault

onset buckets:
  preexisting
  warmup
  pre_emergency
  emergency_entry
  mid_maneuver
  recovery

warm-up modes:
  natural_policy
  steer_probe
  brake_tap
  combined_probe
```

The warm-up period is important because self-identification requires evidence:

```text
command issued -> sensed response -> recurrent state update -> emergency action
```

## Scenario Axes

For each source snapshot, M825 should search obstacle and timing axes:

```text
obstacle_lateral_offset
obstacle_longitudinal_distance / timing
obstacle_half_width
fault_activation_step neighborhood
fault_severity neighborhood when parameterized
source_step neighborhood
```

The goal is not just low clearance. The goal is history-dependent outcome or
action divergence.

## History Variants

M825 should evaluate at least:

```text
normal
reset_hidden_each_step
reset_hidden_then_normal
zero_command_obs
command_shift_obs
response_delay_obs
wrong_cross_fault_history
```

Current `v4_residual_closed_loop_replay` already supports:

```text
zero_command_obs
reset_hidden_each_step
reset_hidden_then_normal
```

`sequence_command_response_intervention` already defines:

```text
command_shift_obs
response_delay_obs
```

M825 may either route through the sequence intervention helper or extend the v4
closed-loop replay helper to support the delayed/shifted variants. Any extension
must be covered by tests.

For `wrong_cross_fault_history`, M825 should pair snapshots whose apparent
geometry is close but fault family differs. Wrong-history injection must be
logged as a diagnostic intervention only; hidden fault labels are never actor
inputs.

## Accepted Row Classes

M825 should emit three accepted row classes.

### Primary Self-ID Rows

Required:

```text
normal history success or finite non-collision margin
wrong/reset/delayed history has lower margin or collision
normal-vs-best-ablation margin gap >= 0.01
normal-vs-wrong action prefix L2 gap >= 0.014 when available
source/fault/onset/warm-up diversity gates pass
```

### Matched Action-Divergent Rows

Required:

```text
current ego state distance below threshold
obstacle geometry distance below threshold
fault family differs
normal action prefix differs materially
wrong-history or reset-history changes margin or action
```

Suggested thresholds:

```text
ego response distance <= 0.08 normalized
obstacle geometry distance <= 0.08 normalized
first-action L2 gap >= 0.02
action-prefix L2 mean gap >= 0.014
```

### Mitigation Rows

Required:

```text
strict success may fail for all variants
normal history still improves margin or impact proxy
normal-vs-ablation margin gap >= 0.02
```

These rows matter because the target driver should mitigate unavoidable crashes,
not only solve avoidable cases.

## Diversity Gates

M825 should use strict source-diversity gates before any training or objective
claim:

```text
accepted primary self-ID rows >= 120
unique seeds >= 16
unique source groups >= 48
unique fault-family pairs >= 8
unique preferred fault families >= 6
unique onset buckets >= 4
unique warm-up modes >= 3
unique scenario axes >= 3
max seed dominance <= 0.20
max source-group dominance <= 0.08
max fault-family-pair dominance <= 0.30
max scenario-axis dominance <= 0.50
```

If M825 cannot meet these gates, it should classify a sampling failure rather
than weakening the thresholds.

## Evidence Metrics

M825 should report:

```text
normal success/collision/margin
reset/zero/delayed/wrong-history success/collision/margin
normal-vs-ablation margin gap
normal-vs-ablation action prefix L2
normal-vs-wrong first-action component deltas
fault family and onset bucket distributions
warm-up mode distributions
source dominance
current-model fault versus proxy-fault counts
mitigation-only counts
```

The main metric is not aggregate success rate. The main metric is:

```text
history-dependent margin/action degradation under matched or source-diverse
hidden dynamics.
```

## Required Artifacts For M825

M825 should write:

```text
src/autodrift/v4_extreme_hidden_dynamics_data_route.py
tests/test_v4_extreme_hidden_dynamics_data_route.py
runs/m825_v4_extreme_hidden_dynamics_data_route/summary.json
runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/history_intervention_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/matched_pair_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/accepted_self_id_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/accepted_mitigation_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/rejected_rows.csv
runs/m825_v4_extreme_hidden_dynamics_data_route/diversity_summary.json
runs/m825_v4_extreme_hidden_dynamics_data_route/gate_summary.csv
docs/m825-v4-extreme-hidden-dynamics-data-route-implementation.md
```

If runtime is too high, M825 may start with a bounded no-training implementation
that still reports coverage shortfall explicitly. It must not turn a smoke run
into a capability claim.

## Result Classes

M825 should classify:

```text
v4_extreme_hidden_dynamics_data_route_pass
v4_extreme_hidden_dynamics_data_route_sparse
v4_extreme_hidden_dynamics_data_route_history_insensitive
v4_extreme_hidden_dynamics_data_route_proxy_only
v4_extreme_hidden_dynamics_data_route_sampling_failure
v4_extreme_hidden_dynamics_data_route_contract_violation
```

Only `pass` may route to an objective or training design. It still must not
promote a checkpoint.

## Decision

Decision:

```text
extreme_hidden_dynamics_data_route_design_admit_m825
```

Next blocker:

```text
m825-v4-extreme-hidden-dynamics-data-route-implementation
```
