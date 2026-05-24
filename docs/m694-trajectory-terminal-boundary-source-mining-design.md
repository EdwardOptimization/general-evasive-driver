# M694 Trajectory-Terminal Boundary Source-Mining Design

## Purpose

M694 starts the `trajectory_terminal_boundary_source_mining` branch selected by
the M693 synthesis.

The new question is:

```text
Can we mine a source surface where small first-action or history-conditioned
differences measurably change closed-loop terminal margin, risk, collision, or
recovery?
```

This milestone is design-only:

```text
no training
no actor update
no residual-head update
no PPO
no checkpoint promotion
no actor-input change
```

## Motivation

M692 showed that the M689 residual heads were implementation-clean and
normal-safe, but closed-loop utility was near zero:

```text
normal_first_action_l2_p95:      0.003928
normal_margin_regression_p95:    0.000008
wrong_risk_improvement_mean:     0.000025
wrong_success_improvement_count: 0
wrong_collision_reduction_count: 0
replay_result_class:             replay_neutral
```

That means the next bottleneck is source quality, not another scalar residual
loss. The project needs source rows that are actually trajectory-sensitive.

## Core Definition

A row is trajectory-sensitive only if the row satisfies all of:

```text
1. The base normal-history rollout is successful or near-boundary, not already
   failed.

2. A small bounded first-action perturbation or counterfactual-history action
   causes a measurable terminal-margin, risk, collision, off-road, spin, or
   recovery-time change.

3. The sensitivity remains visible in a short closed-loop continuation where
   only the first action is overridden and the unchanged base actor controls the
   rest of the rollout.

4. The row belongs to a source-diverse set rather than a single seed, pair,
   surface, time step, or scenario artifact.
```

Rows that are already normal-failed are not action-critical evidence. They can
be logged as hard cases, but they must not be accepted as self-ID source rows.

## Candidate Inputs

M695 should start from the current base actor and existing scenario families:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

surface configs:
  fresh=configs/ppo_m541_matched_l3_variance_4096.json
  ood=configs/eval_m574_moderate_ood_l3.json

optional diagnostic artifacts:
  runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
  runs/m671_response_amplification_shadow/shadow_metadata.csv
```

The M692/M671 artifacts can seed candidate scenarios, but the acceptance decision
must come from fresh closed-loop terminal metrics, not exact output residuals.

## Mining Stages

### Stage A: Normal-History Prepass

Run the base actor and collect snapshots where:

```text
obstacle or boundary interaction is active
episode is not already terminal
normal-history continuation succeeds or is near-boundary
terminal margin is finite
```

Suggested filters:

```text
normal_success == true
normal_collision == false
normal_off_road == false
normal_spin_out == false
normal_margin >= 0.0
normal_margin <= max_boundary_margin
```

Start with:

```text
max_boundary_margin = 0.15
```

Also keep a wider diagnostic bucket:

```text
0.15 < normal_margin <= 0.50
```

but do not count it as boundary accepted unless sensitivity is strong.

### Stage B: Local First-Action Sensitivity

For each prepass snapshot, replay short continuations with bounded one-step
action perturbations:

```text
base_action
steer +/- 0.01
steer +/- 0.02
brake +/- 0.03
throttle +/- 0.03
combined steer/brake pairs
optional M689 residual direction as diagnostic only
```

Each perturbation executes only for the first action:

```text
snapshot -> override first action -> unchanged base actor continuation
```

Record:

```text
best_margin
worst_margin
margin_sensitivity = best_margin - worst_margin
best_risk
worst_risk
risk_sensitivity = worst_risk - best_risk
success_flip_count
collision_flip_count
off_road_flip_count
spin_flip_count
recovery_time_delta
```

Suggested acceptance threshold:

```text
margin_sensitivity >= 0.02
or risk_sensitivity >= 0.02
or any success/collision/off-road/spin flip
```

### Stage C: Counterfactual-History Sensitivity

If a matched wrong-history or paired-history snapshot is available, evaluate:

```text
normal_hidden + base normal action
wrong_hidden + base wrong action
wrong_hidden + normal action
normal_hidden + wrong action
```

Accept a stronger `history_action_critical` label only if:

```text
normal continuation remains successful or near-boundary
wrong/counterfactual continuation worsens margin by >= 0.01
or wrong/counterfactual continuation increases risk by >= 0.01
or wrong/counterfactual continuation creates a collision/off-road/spin flip
```

This label is stronger than simple trajectory sensitivity. The miner should keep
both labels:

```text
trajectory_boundary:
  action perturbations matter in closed loop

history_action_critical:
  counterfactual history or wrong hidden state changes closed-loop outcome

terminal_cliff:
  normal branch has very low positive margin and should become a retention row
```

### Stage D: Source Diversity And Splits

Accepted rows must be source-balanced before they can drive an objective.

Track at least:

```text
surface
scenario config
left seed
right seed or paired seed
physical pair id if available
time step bucket
speed bucket
mu bucket if available only for logging
obstacle-distance bucket
terminal-margin bucket
sensitivity bucket
```

Suggested compact corpus rules:

```text
accepted rows >= 80
trajectory_boundary rows >= 50
history_action_critical rows >= 20 if available
unique seeds >= 20
unique scenario configs >= 2
max single seed dominance <= 10%
max single source bucket dominance <= 25%
heldout split >= 20%
```

Hidden parameters can be used for logging, stratification, and offline analysis,
but must not become actor inputs.

## Required Outputs

M695 should write:

```text
runs/m695_trajectory_terminal_boundary_source_miner/summary.json
runs/m695_trajectory_terminal_boundary_source_miner/candidate_rows.csv
runs/m695_trajectory_terminal_boundary_source_miner/perturbation_rollouts.csv
runs/m695_trajectory_terminal_boundary_source_miner/accepted_rows.csv
runs/m695_trajectory_terminal_boundary_source_miner/source_summary.csv
runs/m695_trajectory_terminal_boundary_source_miner/split_summary.csv
runs/m695_trajectory_terminal_boundary_source_miner/rejected_rows.csv
```

Required summary fields:

```text
rows_attempted
snapshots_collected
normal_success_candidates
normal_failed_rejected
trajectory_sensitive_rows
history_action_critical_rows
terminal_cliff_rows
accepted_rows
heldout_rows
unique_seeds
unique_sources
max_seed_dominance
max_source_dominance
margin_sensitivity_mean
margin_sensitivity_p95
risk_sensitivity_mean
risk_sensitivity_p95
success_flip_count
collision_flip_count
off_road_flip_count
spin_flip_count
actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

## Result Classes

M695 should classify the result as one of:

```text
source_positive:
  accepted_rows and diversity thresholds pass

source_sparse:
  trajectory-sensitive rows exist but not enough diversity or volume

normal_failed_only:
  sensitive rows exist only where the base normal rollout already fails

history_insensitive:
  trajectory-sensitive rows exist but wrong/counterfactual history does not
  change outcomes

surface_empty:
  no meaningful trajectory-sensitive rows are found

implementation_failed:
  snapshots or replay artifacts are incomplete
```

Only `source_positive` can admit an objective-design milestone.

## Negative-Result Interpretation

If the miner finds `source_sparse`, broaden scenario sampling before designing an
objective.

If it finds `normal_failed_only`, the base driver is not strong enough on that
surface; the next task should improve baseline driver capability rather than
claim self-ID proof.

If it finds `history_insensitive`, the surface can still support trajectory
boundary training, but not self-ID claims. In that case the next branch should
separate:

```text
base evasive-driving capability improvement
```

from:

```text
self-identification mechanism evidence
```

## Implementation Notes

Prefer reusing existing replay utilities:

```text
autodrift.matched_history_outcome_gate.collect_requested_outcome_snapshots
autodrift.terminal_margin_recovery_anchor._rollout_first_action_override
autodrift.grounded_capability_action_target_miner.risk_score
```

The implementation should be conservative:

```text
one-step action overrides first
short continuation horizon first
write skipped/rejected rows explicitly
no actor mutation
no residual-head training
no exact-output proxy gate as acceptance
```

## Decision

M694 admits M695 implementation.

Blocked until M695:

```text
actor update
PPO
checkpoint promotion
new residual-head objective
sequence-head deployment
```

## Decision String

```text
trajectory_terminal_boundary_source_mining_design_admit_m695
```

## Next

```text
m695-trajectory-terminal-boundary-source-miner-implementation
```
