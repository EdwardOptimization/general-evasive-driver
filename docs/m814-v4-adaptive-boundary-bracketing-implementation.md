# M814 V4 Adaptive Boundary Bracketing Implementation

## Purpose

M814 implements and runs the no-training adaptive bracketing route designed in
M813.

The question is:

```text
Can deterministic bracket refinement resolve M811 collision/safe edges into
source-diverse primary low-margin rows without weakening alpha, thresholds, or
the actor contract?
```

This milestone is infrastructure-only:

```text
no actor training
no residual-head training
no calibrator training
no optimizer
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_adaptive_boundary_bracketing.py
```

New tests:

```text
tests/test_v4_adaptive_boundary_bracketing.py
```

The implementation reuses the M811 source/warm-up/snapshot generator, then
adds:

- per snapshot-axis collision/safe bracket construction;
- bounded expansion when initial candidates do not bracket;
- deterministic midpoint refinement for continuous obstacle axes;
- primary accepted-row detection at `0.0 <= min_clearance_margin <= 0.00005`;
- balanced accepted-row selection that prioritizes underrepresented axes, seeds, source groups, and fault pairs;
- intervention replay diagnostics for raw accepted rows;
- checksum and no-training invariants.

Refined axes:

```text
obstacle_lateral_offset
obstacle_timing
obstacle_half_width
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_adaptive_boundary_bracketing \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m814_v4_adaptive_boundary_bracketing \
  --alpha 0.2 \
  --primary-margin-threshold 0.00005 \
  --seed-count 12 \
  --max-base-faults 8 \
  --max-fault-specs 14 \
  --max-source-groups 96 \
  --max-snapshots-per-group 2 \
  --min-rows 80 \
  --min-seeds 8 \
  --min-source-groups 16 \
  --min-source-indices 8 \
  --min-fault-pairs 4 \
  --min-warmup-modes 2 \
  --min-boundary-axes 3 \
  --max-seed-dominance 0.25 \
  --max-source-group-dominance 0.15 \
  --max-fault-pair-dominance 0.40 \
  --max-boundary-axis-dominance 0.60 \
  --device cpu
```

## Result

Run directory:

```text
runs/m814_v4_adaptive_boundary_bracketing
```

Summary:

```text
result_class: v4_adaptive_boundary_bracketing_pass
brackets_attempted: 576
brackets_valid: 193
brackets_refined: 193
bracket_status_counts:
  accepted: 101
  max_iterations: 73
  parameter_tolerance: 19
bracket_nonmonotone_count: 0
bracket_expansion_fail_count: 383
bracket_refinement_rows: 2087
replay_errors: 0
warmup_artifact_rows: 0
accepted_primary_raw_rows: 101
accepted_primary_rows: 85
```

Accepted-row diversity:

```text
unique_accepted_seeds: 9
unique_accepted_source_groups: 55
unique_accepted_source_indices: 73
unique_accepted_fault_family_pairs: 8
unique_accepted_warmup_modes: 4
unique_accepted_boundary_axes: 3
max_accepted_seed_dominance: 0.23529411764705882
max_accepted_source_group_dominance: 0.047058823529411764
max_accepted_fault_pair_dominance: 0.23529411764705882
max_accepted_boundary_axis_dominance: 0.5647058823529412
```

Accepted-row axis counts:

```text
obstacle_lateral_offset: 48
obstacle_timing: 25
obstacle_half_width: 12
```

The result passes the pre-registered M813/M814 balance gates:

```text
accepted rows >= 80
unique seeds >= 8
unique source groups >= 16
unique source indices >= 8
unique fault-family pairs >= 4
unique warm-up modes >= 2
unique boundary axes >= 3
max seed dominance <= 0.25
max source-group dominance <= 0.15
max fault-pair dominance <= 0.40
max boundary-axis dominance <= 0.60
at least 10 rows from at least 3 axes
```

## Intervention Diagnostics

M814 replayed interventions for the `101` raw accepted rows:

```text
intervention_replay_rows: 303
reset_hidden_each_step collisions: 69 / 101
reset_hidden_then_normal collisions: 69 / 101
zero_command_obs collisions: 67 / 101
```

These diagnostics are mechanism-positive, but M814 is still only a data-route
milestone. It does not promote a checkpoint and does not admit training by
itself.

## Contract Checks

The run preserved the frozen model invariants:

```text
actor_backbone_changed: false
residual_head_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

## Interpretation

M814 is a clean positive for the M812 diagnosis.

It supports:

- M811 failed because fixed-grid boundary resolution was too coarse;
- adaptive closed-loop bracketing can populate the strict primary band;
- primary rows can be source-diverse and axis-diverse under the frozen actor/residual setup;
- the result does not require actor input changes, threshold weakening, PPO, or checkpoint promotion.

It does not yet prove:

- a calibrated residual gate should be trained immediately;
- the primary rows generalize beyond this current-model/proxy data route;
- true wheel-level failure dynamics are represented;
- a new driver checkpoint should be promoted.

## Decision

Classification:

```text
v4_adaptive_boundary_bracketing_pass
```

M814 does not directly admit calibration, PPO, or promotion.

Next blocker:

```text
m815-v4-adaptive-boundary-bracketing-audit
```

M815 should audit whether this new source/axis-diverse primary corpus is safe
to use for a later residual calibration design, or whether a fresh holdout /
generalization check is required first.

## Verification

```text
python -m compileall -q src/autodrift/v4_adaptive_boundary_bracketing.py tests/test_v4_adaptive_boundary_bracketing.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_adaptive_boundary_bracketing.py
```

Result:

```text
6 passed
```
