# M1148 V4 Public Base Row15 Promoted Actor Update First Replay Design

## Purpose

M1148 designs the first closed-loop replay gate for the M1147 primary
pre-replay candidate.

This milestone is design-only. It does not run replay, train actor weights, run
PPO, build a corpus, run objective sanity, promote a checkpoint, use private
holdout, or change actor inputs.

## Parent Evidence

M1147 selected:

```text
candidate_label: m1147_114602
candidate_checkpoint:
  runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt

base_label: row15_current
base_checkpoint:
  runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

M1147 is only a pre-replay candidate. It passed exact M1144, anchor, and
parameter-scope gates, but no closed-loop replay has been run for this
checkpoint.

## First Replay Scope

M1149 should run first replay on three proof-retention tiers:

```text
old_public_replay
source_diverse_replay
row15_promoted_materialized_replay
```

It should not yet run M1061 family-intersection replay, fresh/OOD eval,
behavior eval, full public gate, PPO, promotion, or private holdout. If first
replay passes, the next milestone may design family-intersection and behavior
diagnostics. If it fails, the next milestone should audit whether failure is
normal-loss, wrong-history-safe, margin-gap regression, row-specific terminal
margin crossing, or metric artifact.

## Replay Surfaces

Old public replay surfaces:

```text
m183_m168:
  runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv

m183_m170:
  runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv

m193_m189:
  runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv

m212_m204:
  runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv

m223_m219:
  runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv

m267_m264:
  runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
```

Source-diverse replay surfaces:

```text
current_m333_surface:
  runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv

m314_continuity_surface:
  runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv

m317_continuity_surface:
  runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
```

Row15-promoted materialized surface:

```text
row15_promoted_materialized:
  runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
```

This last surface checks the exact materialized rows that drove the M1147
objective update. It is not a replacement for old public or source-diverse
replay.

## Gate Settings

All surfaces should use the strict replay-retention thresholds used by the
recent proof gates:

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
  all six old-public surfaces pass

source_diverse_first_replay_pass:
  all three source-diverse surfaces pass

row15_promoted_materialized_replay_pass:
  row15_promoted_materialized passes

first_replay_pass:
  old_public_first_replay_pass
  and source_diverse_first_replay_pass
  and row15_promoted_materialized_replay_pass
```

M1149 should write a compact aggregate summary with:

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
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy row15_current=runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt \
  --checkpoint-policy m1147_114602=runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt \
  --corpus-csv ${CORPUS_CSV} \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy row15_current \
  --candidate-policy m1147_114602 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1149_row15_promoted_actor_update_first_replay/${SURFACE_LABEL}
```

M1149 may run a small aggregation script after the replay commands to classify
surface failures. It must not weaken thresholds after seeing the result.

## Explicit Non-Goals

M1148 and M1149 must not:

- run PPO;
- run actor training;
- run M1061 family-intersection replay before first replay result;
- run full public gate;
- run fresh/OOD or behavior gates;
- promote a checkpoint;
- use private holdout;
- change actor inputs;
- weaken replay thresholds.

## Decision

```text
row15_promoted_first_replay_design_admit_m1149
```

Next milestone:

```text
m1149-v4-public-base-row15-promoted-actor-update-first-replay-run
```
