# M986 V4 Public Base Extreme Near-Cliff Source Mining

## Purpose

M986 follows M985 by narrowing the normal-success mining window to terminal
near-cliff rows:

```text
normal_margin_min: 0.0
normal_margin_max: 0.20
```

Accepted-row action and margin thresholds are unchanged.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M986 does not train, run PPO, promote, use private holdout, or change actor
inputs.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --surface-config low_mu=configs/m984_extreme_low_mu_drop.json \
  --surface-config brake_loss=configs/m984_brake_authority_loss.json \
  --surface-config lateral_loss=configs/m984_lateral_authority_loss.json \
  --surface-config heavy_cg_delay=configs/m984_heavy_cg_delay.json \
  --surface-config high_speed_close=configs/m984_high_speed_close_obstacle.json \
  --surface-seed-range low_mu=98500:98563 \
  --surface-seed-range brake_loss=98580:98643 \
  --surface-seed-range lateral_loss=98660:98723 \
  --surface-seed-range heavy_cg_delay=98740:98803 \
  --surface-seed-range high_speed_close=98820:98883 \
  --sequence-lengths 5,7,9 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 0.20 \
  --max-right-candidates-per-left 64 \
  --max-candidate-pairs-per-surface 1200 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 320 \
  --max-snapshots-per-seed 6 \
  --sample-stride 3 \
  --max-continuation-steps 9 \
  --device auto \
  --run-dir runs/m986_v4_public_base_extreme_near_cliff_source_mining
```

## Result

```text
corpus_passed: false
accepted_rows: 0
snapshot_count: 1137
near_boundary_preferred_snapshots: 60
candidate_pairs: 3527
candidate_rows: 10581
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M986 is negative. It proves that simply focusing the existing extreme family
mining on `normal_margin <= 0.20` is not enough to expose accepted rows.

## Window Coverage

| Surface | Already failed | Near-cliff preferred | Early safe |
| --- | ---: | ---: | ---: |
| brake_loss | 118 | 13 | 114 |
| heavy_cg_delay | 117 | 23 | 125 |
| high_speed_close | 137 | 1 | 3 |
| lateral_loss | 147 | 7 | 84 |
| low_mu | 160 | 16 | 72 |

The near-cliff filter works and still leaves candidates in every family.

## Candidate Outcome

```text
candidate_normal_success_rate: 1.0
candidate_wrong_success_rate: 1.0
candidate_wrong_first_action_threshold_rows: 10581
candidate_wrong_sequence_threshold_rows: 10540
candidate_preferred_rejected_threshold_rows: 10431
candidate_all_action_threshold_rows: 10431
candidate_margin_threshold_rows: 0
candidate_max_margin_gap: 0.002745
```

Top margin-gap row:

```text
surface: lateral_loss
target: unavoidable
left_seed/right_seed: 98718/98688
left_step/right_step: 12/24
normal_margin: 0.114012
wrong_margin: 0.111268
margin_gap: 0.002745
preferred_vs_rejected_action_mean_l2: 0.445056
```

The actor changes actions under wrong history, but the closed-loop continuation
does not degrade enough over the current 9-step horizon.

## Interpretation

Supported:

```text
The M984 families generate near-cliff normal-success rows.
Wrong-history action separation remains live in near-cliff rows.
The 9-step outcome continuation still does not produce success drop or accepted margin gaps.
```

Not supported:

```text
Near-cliff filtering alone is enough to produce a source-diverse proof corpus.
Training should begin from M984-M986.
```

Failure taxonomy:

```text
scenario_sampling_failure
```

## Decision

Do not train. Do not lower accepted-row thresholds. Do not run PPO.

Route to long-horizon outcome audit:

```text
m987-v4-public-base-extreme-near-cliff-long-horizon-audit
```

M987 should keep the same families and near-cliff filter, but increase
`max_continuation_steps` from `9` to `20`. If wrong-history degradation still
does not appear, the branch should pivot to scenario calibration or simulator
fault-extension design rather than more same-parameter mining.

## Artifacts

```text
runs/m986_v4_public_base_extreme_near_cliff_source_mining/summary.json
runs/m986_v4_public_base_extreme_near_cliff_source_mining/snapshot_bank_summary.csv
runs/m986_v4_public_base_extreme_near_cliff_source_mining/normal_window_summary.csv
runs/m986_v4_public_base_extreme_near_cliff_source_mining/candidate_scores.csv
runs/m986_v4_public_base_extreme_near_cliff_source_mining/normal_success_boundary_rows.csv
runs/m986_v4_public_base_extreme_near_cliff_source_mining/normal_success_boundary_corpus.npz
```
