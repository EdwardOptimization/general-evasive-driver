# M1057 V4 Public Base Post Short-Promotion Compact Corpus Conversion Design

## Purpose

M1057 designs compact objective/replay corpus conversion for the refreshed
post-short-promotion wrong-history boundary surface.

This milestone does not run conversion, train, run PPO, use private holdout,
change actor inputs, or promote a checkpoint.

## Input Surface

Use the M1056 `0.005m` diagnostic robustness pass:

```text
runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv
```

This surface has:

```text
accepted_wrong_rows: 315
physical_pairs: 15
left_steps: 7
checkpoints: 3
targets: 3
margin_buckets_at_0.005m: 2
success_drop_fraction: 1.0
max_pair_fraction: 0.190476
```

## Conversion Family

Convert the same accepted-row surface for all three short-PPO family
checkpoints:

```text
short61049_current:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051_repeat:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

## Compact Corpus Rule

M1058 should use:

```text
max_rows_per_physical_pair: 2
min_compact_rows: 20
min_physical_pairs: 10
min_targets: 2
optimization_seeds: 10570,10571,10572
steps: 180
batch_size: 64
learning_rate: 0.0003
weight_decay: 0.001
hidden_dim: 96
```

The compact corpus should not include more than two rows from any physical pair.
If the conversion produces fewer than `20` rows or fewer than `10` physical
pairs for a source checkpoint, M1058 must classify the result as compact-corpus
sparse rather than lowering caps.

## Objective Sanity Commands

Current base:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 2 \
  --optimization-seeds 10570,10571,10572 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m1058_short61049_boundary_outcome_corpus_seed10570
```

Repeat checkpoints:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 2 \
  --optimization-seeds 10570,10571,10572 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m1058_short61050_boundary_outcome_corpus_seed10570

OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_corpus_objective \
  --checkpoint-policy short61051=runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --boundary-rows-csv runs/m1056_margin_bucket_width_0005/accepted_wrong_history_rows.csv \
  --delay-steps 10 \
  --device cpu \
  --max-rows-per-physical-pair 2 \
  --optimization-seeds 10570,10571,10572 \
  --steps 180 \
  --batch-size 64 \
  --learning-rate 0.0003 \
  --weight-decay 0.001 \
  --hidden-dim 96 \
  --run-dir runs/m1058_short61051_boundary_outcome_corpus_seed10570
```

## Replay Sanity Commands

M1058 should run cross-family replay sanity:

```text
short61049 corpus:
  baseline short61049, candidate short61050

short61050 corpus:
  baseline short61050, candidate short61049

short61051 corpus:
  baseline short61051, candidate short61049
```

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_outcome_replay_gate \
  --checkpoint-policy short61049=runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --checkpoint-policy short61050=runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt \
  --corpus-csv runs/m1058_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --max-continuation-steps 60 \
  --baseline-policy short61049 \
  --candidate-policy short61050 \
  --max-normal-success-drop 0.0 \
  --max-normal-margin-regression 0.005 \
  --max-margin-gap-regression 0.001 \
  --max-success-drop-count-regression 0 \
  --device cpu \
  --run-dir runs/m1058_short61049_replay_sanity_seed10570
```

M1058 should use analogous commands for `short61050` and `short61051`.

## Acceptance

M1058 passes only if:

```text
three compact corpora are created;
each corpus has >= 20 rows;
each corpus has >= 10 physical pairs;
each corpus has >= 2 targets;
objective sanity passes for all three checkpoints and all optimization seeds;
replay sanity preserves normal success and wrong-history failure for all three;
actor inputs unchanged;
training_started == false;
ppo_used == false;
promoted == false;
private_holdout_used == false.
```

If M1058 passes, it should route to a post-refresh conversion audit or gate
integration design, not directly to PPO.

## Decision

```text
post_short_promotion_compact_corpus_conversion_design_admit_m1058_conversion
```

Next:

```text
m1058-v4-public-base-post-short-promotion-compact-corpus-conversion
```
