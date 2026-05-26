# M985 V4 Public Base Extreme Scenario Family Source Mining

## Purpose

M985 runs the first larger no-PPO source mining pass across the five M984
extreme scenario families.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M985 does not train, run PPO, promote, use private holdout, change actor inputs,
or relax accepted-row thresholds.

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
  --normal-margin-max 1.0 \
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
  --run-dir runs/m985_v4_public_base_extreme_scenario_family_source_mining
```

## Result

```text
corpus_passed: false
accepted_rows: 0
snapshot_count: 1137
near_boundary_preferred_snapshots: 246
candidate_pairs: 5056
candidate_rows: 15168
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M985 is a negative source-mining result, not an infrastructure failure.

## Family Coverage

Snapshot summary:

| Surface | Snapshots | Seeds | Targets | Obstacle distance mean |
| --- | ---: | ---: | ---: | ---: |
| brake_loss | 245 | 64 | 3 | 2.881978 |
| heavy_cg_delay | 265 | 64 | 3 | 2.916279 |
| high_speed_close | 141 | 64 | 1 | 3.371824 |
| lateral_loss | 238 | 64 | 3 | 3.057937 |
| low_mu | 248 | 64 | 3 | 3.202267 |

Normal-window summary:

| Surface | Already failed | Near-boundary preferred | Early safe |
| --- | ---: | ---: | ---: |
| brake_loss | 118 | 68 | 59 |
| heavy_cg_delay | 117 | 66 | 82 |
| high_speed_close | 137 | 4 | 0 |
| lateral_loss | 147 | 43 | 48 |
| low_mu | 160 | 65 | 23 |

The new scenario families produce many valid windows. The issue is not missing
sampling coverage.

## Candidate Outcome

```text
candidate_normal_success_rate: 1.0
candidate_wrong_success_rate: 1.0
candidate_wrong_first_action_threshold_rows: 15168
candidate_wrong_sequence_threshold_rows: 15126
candidate_preferred_rejected_threshold_rows: 15019
candidate_all_action_threshold_rows: 15019
candidate_margin_threshold_rows: 0
candidate_all_action_and_margin_threshold_rows: 0
candidate_max_margin_gap: 0.004403
```

All wrong-history continuations remain successful. The strongest positive
margin gaps are in `heavy_cg_delay`, but remain below the `0.010` accepted-row
margin threshold. The top rows have strong action separation and normal margins
around `0.70`, which is too much terminal slack for outcome-sensitive proof.

## Interpretation

M985 supports the scenario-family branch as a sampler, but not yet as a proof
corpus generator.

Supported:

```text
The five M984 families can generate broad hidden-dynamics emergency scenarios.
Wrong-history action separation is live under these families.
The current broad normal-margin window mostly samples rows with too much terminal slack.
```

Not supported:

```text
M984 families already expose source-diverse outcome-sensitive wrong-history rows under normal_margin_max=1.0.
Training or PPO should start from this branch.
```

Failure taxonomy:

```text
scenario_sampling_failure
```

## Decision

Do not train. Do not lower accepted-row thresholds. Do not run PPO.

Route to near-cliff mining:

```text
m986-v4-public-base-extreme-near-cliff-source-mining
```

M986 should keep the same five families and seed ranges, but restrict
`normal_margin_max` to `0.20`. This targets terminal-margin near-cliff states
without weakening the accepted-row thresholds.

## Artifacts

```text
runs/m985_v4_public_base_extreme_scenario_family_source_mining/summary.json
runs/m985_v4_public_base_extreme_scenario_family_source_mining/snapshot_bank_summary.csv
runs/m985_v4_public_base_extreme_scenario_family_source_mining/normal_window_summary.csv
runs/m985_v4_public_base_extreme_scenario_family_source_mining/candidate_scores.csv
runs/m985_v4_public_base_extreme_scenario_family_source_mining/normal_success_boundary_rows.csv
runs/m985_v4_public_base_extreme_scenario_family_source_mining/normal_success_boundary_corpus.npz
```
