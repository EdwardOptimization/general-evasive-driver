# M980 V4 Public Base Post Repair Surface Refresh Implementation

## Purpose

M980 runs the no-PPO current-base surface refresh designed in M979.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M980 does not train, run PPO, promote, use private holdout, change actor inputs,
or relax thresholds.

## Command

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

## Result

```text
corpus_passed: false
accepted_rows: 30
near_boundary_preferred_snapshots: 301
candidate_pairs: 4000
candidate_rows: 12000
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M980 is a narrow positive, not a corpus pass.

It finds real wrong-history-sensitive near-boundary rows under the new M974
public base, unlike the older M667 run on BC5660. However, the accepted rows are
not source-diverse enough to use as a durable training/proof corpus.

## Window Coverage

| Surface | Window class | Rows | Seeds | Targets | Mean normal margin |
| --- | --- | ---: | ---: | ---: | ---: |
| fresh | near_boundary_preferred | 140 | 43 | 2 | 0.470507 |
| fresh | early_safe_diagnostic | 299 | 70 | 3 | 2.620738 |
| fresh | already_failed_diagnostic | 66 | 22 | 2 | -0.109280 |
| ood | near_boundary_preferred | 161 | 55 | 3 | 0.520081 |
| ood | early_safe_diagnostic | 156 | 47 | 3 | 2.468567 |
| ood | already_failed_diagnostic | 87 | 29 | 2 | -0.097919 |

The refresh is not blocked by missing near-boundary preferred windows.

## Accepted Rows

Accepted rows:

```text
accepted_rows: 30
accepted_success_drop_rate: 1.0
mean_preferred_vs_rejected_action_mean_l2: 0.138704
mean_margin_gap: 0.000333
```

The action effect is strong, and all accepted rows are success-drop rows.

But source diversity is too narrow:

```text
accepted_left_seeds: 1
accepted_right_seeds: 2
accepted_physical_pairs: 2
max_left_seed_share: 1.0
max_physical_pair_share: 0.5
target: unavoidable only
surface: ood only
left_seed: 98107 only
right_seeds: 98108, 98139
```

So the corpus fails the pre-registered thresholds:

```text
accepted_rows >= 40                  false
accepted_physical_pairs >= 8          false
accepted_left_seeds >= 6              false
accepted_right_seeds >= 6             false
source_holdout_nonempty               true
```

## Interpretation

M980 falsifies the strongest negative interpretation from M667:

```text
wrong-history outcome sensitivity is absent under fresh normal-success windows
```

That is now false for the M974 public base. M980 found outcome-sensitive rows
with large action separation.

But M980 does not produce a usable surface corpus. The accepted rows are a
source-narrow pocket around one OOD left seed.

Classification:

```text
post_repair_surface_refresh_source_narrow_positive
```

## Decision

Do not train from the M980 corpus. Do not lower thresholds. Do not run PPO.

Route to expanded source refresh:

```text
m981-v4-public-base-post-repair-expanded-source-refresh
```

M981 should keep the same thresholds, expand seed/source coverage, and ask
whether the M980 pocket generalizes into a source-diverse current-base surface.

## Artifacts

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
