# M1034 V4 Public Base Candidate B M183 Row16 Active-Set Anchor Export

## Purpose

M1034 implements and runs the no-update anchor export designed in M1033.

It exports Candidate B's normal-history trajectory on M183/M170 row16 as an
exact-loadable `TrajectoryActionAnchor`.

M1034 does not run repair, PPO, training, private holdout, promotion, first
replay, or actor-input changes.

## Implementation

New tooling:

```text
src/autodrift/m183_row16_active_set_anchor_export.py
tests/test_m183_row16_active_set_anchor_export.py
```

Command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.m183_row16_active_set_anchor_export \
  --run-dir runs/m1034_candidate_b_m183_row16_active_set_anchor_export \
  --device auto
```

## Inputs

Checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Corpus:

```text
runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv
row_id: 16
```

Env config:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

## Artifacts

```text
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/summary.json
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.npz
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/m183_row16_normal_trajectory_anchor.csv
runs/m1034_candidate_b_m183_row16_active_set_anchor_export/row16_replay_sanity.csv
```

## Result

M1034 passes:

```text
result_class: m183_row16_active_set_anchor_export_pass
selected_rows: 1
anchor_rows: 57
normal_branch_only: true
actor_inputs_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Anchor tensor shapes:

```text
observation:       57 x 72
hidden:            57 x 128
reference_action:  57 x 3
source_index:      57
step_index:        57
weight:            57
```

Replay sanity for row16:

```text
normal_success: true
wrong_history_success: false
normal_margin: 0.001315984
wrong_history_margin: -0.005083863
```

The exported anchor is therefore the intended normal branch for the active-set
failure identified in M1032.

## Interpretation

M1034 converts the M183/M170 row16 blocker from a narrative gate into exact
training/evaluation data.

The next repair/projection step can now use a combined active-set anchor:

```text
M293 current-family rejected-history trajectory anchor
+
M1034 M183/M170 row16 normal trajectory anchor
```

This should prevent a repeat of the M1031 pattern:

```text
M267/M264 row15 retained, but M183/M170 row16 normal branch crosses the
terminal-margin boundary.
```

## Decision

```text
candidate_b_m183_row16_active_set_anchor_export_pass
```

Next milestone:

```text
m1035-v4-public-base-candidate-b-combined-active-set-repair-design
```
