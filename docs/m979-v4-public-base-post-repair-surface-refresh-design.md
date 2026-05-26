# M979 V4 Public Base Post Repair Surface Refresh Design

## Purpose

M979 designs a fresh proof/preference surface refresh around the new
public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

This is required before another guarded PPO continuation. M972-M977 used and
repaired against established public proof surfaces. M978 therefore classified
public-gate overfit risk as `moderate` and required a fresh current-base surface
refresh first.

M979 does not run PPO, train, promote, use private holdout, or change actor
inputs.

## Design Question

Ask whether the new public-gate base still exposes fresh, source-diverse
wrong-history proof/preference rows outside the repeatedly optimized M267/M264
surface.

The refresh should answer:

```text
Are there M974-family wrong-history rows where normal history succeeds,
wrong history degrades action or margin, and sources are diverse enough to
support exact preference/proof objectives before any new PPO?
```

## Why Not Start PPO Immediately

M972 already showed the risk:

```text
PPO can retain fresh/behavior metrics while washing out wrong-history proof.
```

M974/M976 repaired and promoted a small base-start exact update, but that does
not prove future PPO will preserve fresh surfaces. Starting PPO now would
optimize against old public rows again.

## Refresh Tool

M980 should first reuse:

```bash
python -m autodrift.normal_success_boundary_source_miner
```

This miner is appropriate because it:

1. collects decision-window snapshots under the current checkpoint;
2. filters left snapshots to normal-success near-boundary windows;
3. pairs them with compatible wrong-history right snapshots;
4. scores preferred versus rejected action sequences;
5. writes source-diverse rows and an NPZ corpus without training.

M667 previously found near-boundary normal-success windows but no accepted rows
for the old BC5660 actor. That negative result is not assumed to carry over to
the M974 public-gate base.

## Surface Scope

Use public workflow distributions only:

```text
fresh: configs/ppo_m541_matched_l3_variance_4096.json
ood:   configs/eval_m574_moderate_ood_l3.json
```

Use fresh seed ranges that are not the old M667 seed ranges:

```text
fresh: 98000-98079
ood:   98100-98179
```

This is still public workflow evidence, not private holdout.

## M980 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --surface-seed-range fresh=98000:98079 \
  --surface-seed-range ood=98100:98179 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 64 \
  --max-candidate-pairs-per-surface 2000 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 640 \
  --max-snapshots-per-seed 8 \
  --sample-stride 3 \
  --max-continuation-steps 9 \
  --device auto \
  --run-dir runs/m980_v4_public_base_post_repair_surface_refresh
```

## Acceptance Thresholds

M980 should classify the refresh as positive only if:

```text
near_boundary_preferred_snapshots >= 40
accepted_rows >= 40
accepted_physical_pairs >= 8
accepted_left_seeds >= 6
accepted_right_seeds >= 6
source_holdout_nonempty == true
mean_preferred_vs_rejected_action_mean_l2 >= 0.010
mean_margin_gap >= 0.010 or accepted_success_drop_rate >= 0.25
actor_parameters_changed == false
ppo_used == false
```

Also report diversity diagnostics:

```text
max_physical_pair_share
max_left_seed_share
max_source_index_share
target_summary
split_summary
```

## Route Logic

If M980 is positive:

```text
route to compact corpus / exact objective sanity
```

The next step should convert accepted rows into an explicit current-base
preference/proof corpus and test exact objective sanity before any PPO.

If M980 finds near-boundary windows but no accepted rows:

```text
route to action/outcome sensitivity audit
```

That would mean the new public base, like BC5660 in M667, has valid preferred
windows but insufficient wrong-history outcome effect under this surface.

If M980 finds too few near-boundary windows:

```text
route to scenario/source expansion
```

That would mean the current seed/config window is not exposing handling-limit
near-boundary states.

## Non-Goals

M979/M980 must not:

- run PPO;
- change actor inputs;
- promote a checkpoint;
- use private holdout;
- lower action/margin thresholds after seeing results;
- count old public rows as fresh surface evidence.

## Required Artifacts

```text
runs/m980_v4_public_base_post_repair_surface_refresh/summary.json
runs/m980_v4_public_base_post_repair_surface_refresh/snapshot_bank_summary.csv
runs/m980_v4_public_base_post_repair_surface_refresh/normal_window_summary.csv
runs/m980_v4_public_base_post_repair_surface_refresh/candidate_scores.csv
runs/m980_v4_public_base_post_repair_surface_refresh/normal_success_boundary_rows.csv
runs/m980_v4_public_base_post_repair_surface_refresh/normal_success_boundary_corpus.npz
runs/m980_v4_public_base_post_repair_surface_refresh/source_summary.csv
runs/m980_v4_public_base_post_repair_surface_refresh/split_summary.csv
runs/m980_v4_public_base_post_repair_surface_refresh/target_summary.csv
```

## Decision

Admit:

```text
m980-v4-public-base-post-repair-surface-refresh-implementation
```

Decision:

```text
post_repair_surface_refresh_design_admit_m980
```
