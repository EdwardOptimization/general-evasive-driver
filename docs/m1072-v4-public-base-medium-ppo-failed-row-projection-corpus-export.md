# M1072 V4 Public Base Medium PPO Failed-Row Projection Corpus Export

## Purpose

M1072 exports a source-labeled projection corpus for the M1069 medium PPO proof
washout. It does not run PPO, optimize actor weights, promote, or use private
holdout.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.medium_ppo_failed_row_projection_corpus \
  --run-dir runs/m1072_medium_ppo_failed_row_projection_corpus \
  --device auto
```

## Result

```text
result_class: medium_ppo_failed_row_projection_corpus_pass
rows: 22
surfaces: 8
source_policy_count: 4
source_checkpoint_count: 3
actor_inputs_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
private_holdout_used: false
```

Artifacts:

```text
runs/m1072_medium_ppo_failed_row_projection_corpus/summary.json
runs/m1072_medium_ppo_failed_row_projection_corpus/failed_row_map.csv
runs/m1072_medium_ppo_failed_row_projection_corpus/current_family_conflict_corpus.npz
```

The exported NPZ loads through `load_current_family_conflict_snippets` with the
P0 actor contract:

```text
rows: 22
obs_dim: 72
hidden_dim: 128
act_dim: 3
```

## Surface Coverage

```text
m183_m168: 2 rows
m183_m170: 1 row
m267_m264: 1 row
short61049_family_intersection: 4 rows
short61050_family_intersection: 6 rows
short61051_family_intersection: 6 rows
m317_continuity_surface: 1 row
m314_continuity_surface: 1 row
```

This includes every failed row identified by M1070:

```text
old public:
  m183_m168 rows 9,10
  m183_m170 row 10
  m267_m264 row 15

M1061 family-intersection:
  short61049 rows 16,22,23,24
  short61050 rows 16,17,23,24,25,26
  short61051 rows 16,17,23,24,25,26

source-diverse:
  m317 row 15
  m314 row 15
```

## Source Labels

The corpus preserves source identity in `failed_row_map.csv`:

```text
surface
source_policy
source_checkpoint
boundary_npz
boundary_csv
replay_rows_csv
row_id
physical_pair_key
source_wrong_history_margin
raw_wrong_history_margin
raw_normal_margin
weight
preferred anchor action
rejected anchor action
```

Source checkpoints:

```text
m399_base / short61049:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt

short61050:
  runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt

short61051:
  runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
```

This matters because M1069 failed across the current short-PPO family, not only
against the M1049 base.

## Margin And Weight Diagnostics

```text
raw_wrong_margin_min: 0.0000293021
raw_wrong_margin_max: 0.0011632398
weight_sum: 0.1695915091
margin_floor: 0.0001
max_weight: 20.0
```

The failed wrong-history margins are small positive margins, matching the M1070
diagnosis: M1069 made the wrong-history branch marginally safe rather than
destroying normal-history behavior.

## Implementation Note

Added module:

```text
src/autodrift/medium_ppo_failed_row_projection_corpus.py
```

The module maps failed rows back to source boundary NPZ/CSV artifacts, computes
source-policy preferred and rejected deterministic actions, writes a combined
`current_family_conflict_corpus.npz`, and validates it with the existing loader.

## Decision

```text
medium_ppo_failed_row_projection_corpus_pass_route_to_projection_probe
```

Next:

```text
m1073-v4-public-base-medium-ppo-failed-row-repair-projection-probe
```
