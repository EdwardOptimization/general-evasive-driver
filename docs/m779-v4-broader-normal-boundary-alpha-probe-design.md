# M779 V4 Broader Normal-Boundary Alpha Probe Design

## Purpose

M779 designs the no-training alpha-boundary probe admitted by M778.

The question is:

```text
Can the M761 residual head keep strict normal retention on the broader M773
corpus at an alpha below 0.2 while still improving intervention sensitivity?
```

This design exists because M777 alpha `0.2` was mechanism-positive but failed
strict normal retention on one near-boundary source:

```text
seed: 77025
source_index: 12
step: 24
preferred_fault: halfshaft_torque_loss_proxy
fault_family_pair: drive_authority_drop->rear_lateral_authority_drop
base normal margin: +0.000124
alpha 0.2 normal margin: -0.000062
```

M779 is design-only:

```text
no replay run
no actor training
no residual retraining
no optimizer
no PPO
no checkpoint promotion
```

## Registered Inputs

M780 should use the same actor, residual head, broader corpus, and scenario
config as M777:

```text
checkpoint:
  runs/m568_scaled_l3_bc_seed5660/checkpoint.pt

residual head:
  runs/m761_v4_sequence_objective_probe/residual_head.pt

positive rows:
  runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv

contrast rows:
  runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv

scenario config:
  configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json
```

M780 must preserve:

```text
no actor mutation
no residual parameter mutation
no optimizer
no PPO
no promotion
current_model_or_proxy claim boundary
M773 hard-negative sparsity caveat
M777 alpha 0.2 strict-normal-retention failure
```

## Registered Alpha Ladder

M780 should run:

```text
alphas:
  0.0
  0.05
  0.10
  0.125
  0.15
  0.175
  0.20
```

Rationale:

```text
alpha 0.0:
  base reference

alpha 0.05 and 0.10:
  conservative lower-alpha probes

alpha 0.125:
  near the estimated margin boundary implied by source 77025/source_index 12

alpha 0.15 and 0.175:
  bracket the transition toward the known alpha 0.2 failure

alpha 0.20:
  failed reference from M777, retained for comparability
```

The ladder is pre-registered here. M780 must not select or add alphas after
seeing probe outcomes.

## Registered Command

M780 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_residual_closed_loop_replay \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --positive-rows runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_broader_holdout_scenarios.json \
  --run-dir runs/m780_v4_broader_normal_boundary_alpha_probe \
  --device cpu \
  --alphas 0.0,0.05,0.1,0.125,0.15,0.175,0.2
```

## Required Metrics

M780 must report the existing replay metrics:

```text
sample_reconstruction_success_rate
metadata_missing_rows
rejected_rows
normal_success_rate
normal_collision_rate
normal_margin_regression_mean_vs_base
normal_margin_regression_p95_vs_base
normal_first_action_drift_mean_vs_base
normal_first_action_drift_p95_vs_base
intervention_action_gap_mean_vs_normal
intervention_action_gap_p10_vs_normal
normal_minus_intervention_margin_gap_mean
outcome_sensitivity_retention_rate
intervention_success_rate
intervention_collision_rate
hard_negative_available_fraction
```

M780 must also stratify the normal boundary source:

```text
seed 77025
source_index 12
step 24
preferred_fault halfshaft_torque_loss_proxy
fault_family_pair drive_authority_drop->rear_lateral_authority_drop
```

For that source, report by alpha:

```text
normal success/collision
normal min_clearance_margin
first_action_drift_vs_base_normal
prefix_l2_mean_vs_base_normal
first residual vector
duplicated row count by variant/horizon
```

## Strict Feasibility Criteria

A lower alpha may be called strict-retention feasible only if all hold:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
normal_success_rate == 1.0
normal_collision_rate == 0.0
intervention_action_gap_mean_vs_normal > base_intervention_action_gap_mean
intervention_action_gap_p10_vs_normal >= base_intervention_action_gap_p10
normal_minus_intervention_margin_gap_mean > base_margin_gap_mean
outcome_sensitivity_retention_rate == 1.0
actor_backbone_changed == false
optimizer_started == false
training_started == false
ppo_used == false
promoted == false
```

This is still not a promotion gate. It is only an alpha-feasibility diagnostic.

## Decision Branches for M780 Audit

If a lower alpha satisfies strict feasibility:

```text
M781 should audit it as a limited broader alpha-feasibility result.
Do not promote a checkpoint.
Do not run PPO.
Decide whether the feasible alpha is strong enough to justify a repaired
residual objective or another broader holdout replay.
```

If all useful alphas still collide at source `77025/source_index 12`:

```text
M781 should classify this as normal-margin retention failure and design
explicit normal-margin retention or boundary-source repair.
```

If strict-retention alphas pass but lose intervention sensitivity:

```text
M781 should classify this as residual scale/objective insufficiency and pivot
to residual objective redesign rather than PPO.
```

If additional normal sources fail:

```text
M781 should classify this as broader behavior regression and return to
source-balanced mining plus normal-retention objective design.
```

## Supported Claims

M779 supports:

```text
1. The next experiment is pre-registered rather than retroactively tuning alpha.

2. The M777 alpha 0.2 failure remains the blocker and reference point.

3. The probe directly tests whether M777's failure is a narrow alpha-boundary
   issue or an objective-design issue.
```

## Forbidden Claims

M779 does not claim:

```text
1. A lower alpha is safe.

2. The residual head is ready for PPO.

3. A driver checkpoint can be promoted.

4. The current single-track proxy faults are true wheel blowout, halfshaft, or
   four-wheel physics.
```

## Decision

Decision:

```text
normal_boundary_alpha_probe_design_admit_m780
```

Next blocker:

```text
m780-v4-broader-normal-boundary-alpha-probe-implementation
```

PPO, checkpoint promotion, residual retraining, and broad generalization claims
remain blocked.
