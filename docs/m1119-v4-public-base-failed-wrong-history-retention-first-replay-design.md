# M1119 V4 Public Base Failed Wrong-History Retention First Replay Design

## Purpose

M1119 designs the first closed-loop replay gate for the M1118 best pre-replay
candidate.

This milestone is design-only. It does not run replay, train actor weights, run
PPO, promote a checkpoint, use private holdout, or change actor inputs.

## Parent Evidence

M1118 selected:

```text
candidate_label: m1118_seed111800
candidate_checkpoint: runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt
base_checkpoint: runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

M1118 is only a pre-replay candidate. It passed exact and anchor gates, but no
closed-loop replay has been run for this checkpoint.

## First Replay Scope

M1120 should run first replay only on target-base proof surfaces that failed in
M1112. These rows are represented in the current public-base hidden-state space
and were directly targeted by the M1115 retention anchor.

Old public replay surfaces:

```text
m183_m168:
  corpus: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv

m223_m219:
  corpus: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv

m267_m264:
  corpus: runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

Source-diverse replay surfaces:

```text
current_m333_surface:
  corpus: runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv

m314_continuity_surface:
  corpus: runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv

m317_continuity_surface:
  corpus: runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
```

M1120 should not run full public replay, family-intersection replay, fresh/OOD
eval, behavior eval, PPO, promotion, or private holdout. If target-base first
replay passes, the next milestone may design the family-intersection replay
diagnostic. If it fails, the next milestone should audit whether failure is
normal-loss, wrong-history-safe, margin-gap regression, or metric artifact.

## Gate Settings

All surfaces should use the same strict retention thresholds as M1112:

```text
max_continuation_steps: 60
max_normal_success_drop: 0.0
max_normal_margin_regression: 0.005
max_margin_gap_regression: 0.001
max_success_drop_count_regression: 0
```

Required pass conditions:

```text
old_public_first_replay_pass:
  all three old-public surfaces pass

source_diverse_first_replay_pass:
  all three source-diverse surfaces pass

target_base_first_replay_pass:
  old_public_first_replay_pass and source_diverse_first_replay_pass
```

M1120 should write a compact aggregate summary with:

```text
surface_label
surface_tier
rows
baseline_success_drop_count
candidate_success_drop_count
normal_success_delta
wrong_history_success_delta
normal_margin_mean_delta
margin_gap_mean_delta
gate_pass
failure_class
```

Failure classes:

```text
normal_lost:
  candidate loses normal-history success.

wrong_history_safe:
  candidate keeps normal success but wrong-history branch becomes safe.

margin_gap_regression:
  success-drop count holds but margin gap regresses beyond threshold.

metric_artifact:
  failure is inconsistent with row-level margins and needs audit.

none:
  surface passes.
```

## Command Template

Use `autodrift.boundary_outcome_replay_gate` for each surface:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy m399_base=runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt \
  --checkpoint-policy m1118_seed111800=runs/m1118_failed_wrong_history_retention_actor_update_seed111800/optimized_checkpoint.pt \
  --corpus-csv ${CORPUS_CSV} \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy m399_base \
  --candidate-policy m1118_seed111800 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1120_failed_wrong_history_retention_first_replay/${SURFACE_LABEL}
```

## Explicit Non-Goals

M1119 and M1120 must not:

- run PPO;
- run actor training;
- run family-intersection replay before target-base first replay result;
- run full public gate;
- run fresh/OOD or behavior gates;
- promote a checkpoint;
- use private holdout;
- change actor inputs;
- weaken replay thresholds.

## Decision

```text
failed_wrong_history_retention_first_replay_design_admit_target_base_first_replay
```

Next milestone:

```text
m1120-v4-public-base-failed-wrong-history-retention-first-replay-run
```
