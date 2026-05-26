# M981 V4 Public Base Post Repair Expanded Source Refresh

## Purpose

M981 expands the M980 post-repair source refresh while keeping the same
acceptance thresholds. It tests whether the M980 accepted pocket becomes a
source-diverse current-base wrong-history surface under broader fresh public
seed coverage.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M981 does not train, run PPO, promote, use private holdout, change actor inputs,
or lower the M980 thresholds.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --surface-seed-range fresh=98200:98319 \
  --surface-seed-range ood=98320:98479 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 96 \
  --max-candidate-pairs-per-surface 5000 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 1200 \
  --max-snapshots-per-seed 8 \
  --sample-stride 3 \
  --max-continuation-steps 9 \
  --device auto \
  --run-dir runs/m981_v4_public_base_post_repair_expanded_source_refresh
```

## Result

```text
corpus_passed: false
accepted_rows: 0
near_boundary_preferred_snapshots: 465
snapshot_count: 1564
candidate_pairs: 10000
candidate_rows: 30000
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M981 is a negative expanded-source result. It finds plenty of near-boundary
windows and strong action separation, but no wrong-history continuation causes
success drop or enough margin degradation.

## Window Coverage

| Surface | Window class | Rows | Seeds | Targets | Mean normal margin |
| --- | --- | ---: | ---: | ---: | ---: |
| fresh | near_boundary_preferred | 208 | 70 | 2 | 0.432757 |
| fresh | early_safe_diagnostic | 419 | 106 | 3 | 2.559660 |
| fresh | already_failed_diagnostic | 114 | 38 | 2 | -0.078777 |
| ood | near_boundary_preferred | 257 | 91 | 2 | 0.519566 |
| ood | early_safe_diagnostic | 395 | 98 | 3 | 2.693089 |
| ood | already_failed_diagnostic | 171 | 57 | 2 | -0.105774 |

The failure is not caused by missing near-boundary preferred windows.

## Candidate Outcome

```text
candidate_normal_success_rate: 1.0
candidate_wrong_success_rate: 1.0
candidate_wrong_first_action_threshold_rows: 30000
candidate_wrong_sequence_threshold_rows: 29994
candidate_preferred_rejected_threshold_rows: 29959
candidate_all_action_threshold_rows: 29959
candidate_margin_threshold_rows: 0
candidate_all_action_and_margin_threshold_rows: 0
candidate_max_margin_gap: 0.004490
```

Rejection reasons:

```text
no_success_drop_or_margin_gap: 29959
preferred_rejected_action_mean_l2_below_threshold;no_success_drop_or_margin_gap: 35
wrong_action_sequence_mean_l2_below_threshold;preferred_rejected_action_mean_l2_below_threshold;no_success_drop_or_margin_gap: 6
```

The top positive margin-gap candidates still remain below the M980 threshold.
For example, the best row is:

```text
surface: fresh
target: drift_required
left_seed/right_seed: 98224/98264
left_step/right_step: 42/51
normal_margin: 0.071442
wrong_margin: 0.066953
margin_gap: 0.004490
preferred_vs_rejected_action_mean_l2: 0.412988
normal/wrong terminal: continuation_limit / continuation_limit
```

## Interpretation

M981 does not support using the M980 rows as a broad current-base surface.
Under a larger fresh/OOD seed pass, the actor frequently produces different
actions under wrong history, but those wrong-history actions remain successful.

This means M980 is currently best treated as a narrow positive pocket, not a
source-diverse proof corpus. The result does not falsify wrong-history outcome
sensitivity entirely, because M980 found a deterministic OOD pocket, but it
does show that ordinary expanded seed coverage does not expose that sensitivity
often enough.

Classification:

```text
post_repair_expanded_source_refresh_empty_outcome_sensitive_surface
```

Failure taxonomy:

```text
scenario_sampling_failure
```

## Decision

Do not train. Do not lower thresholds. Do not run PPO.

Route to a targeted OOD pocket expansion audit:

```text
m982-v4-public-base-post-repair-ood-pocket-expansion-audit
```

M982 should return to the M980 OOD seed range and increase candidate/source
coverage. This distinguishes a candidate-limit artifact from a genuinely
isolated OOD pocket before the branch moves to new scenario-family generation.

## Artifacts

```text
runs/m981_v4_public_base_post_repair_expanded_source_refresh/summary.json
runs/m981_v4_public_base_post_repair_expanded_source_refresh/snapshot_bank_summary.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/normal_window_summary.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/candidate_scores.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/normal_success_boundary_rows.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/normal_success_boundary_corpus.npz
runs/m981_v4_public_base_post_repair_expanded_source_refresh/source_summary.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/split_summary.csv
runs/m981_v4_public_base_post_repair_expanded_source_refresh/target_summary.csv
```
