# M987 V4 Public Base Extreme Near-Cliff Long-Horizon Audit

## Purpose

M987 tests whether M986 missed delayed wrong-history failures because the
continuation horizon was only 9 steps. It keeps the same five M984 scenario
families and near-cliff normal-success window, but increases:

```text
max_continuation_steps: 9 -> 20
```

Accepted-row thresholds are unchanged.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M987 does not train, run PPO, promote, use private holdout, or change actor
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
  --max-continuation-steps 20 \
  --device auto \
  --run-dir runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit
```

## Result

```text
corpus_passed: false
accepted_rows: 0
snapshot_count: 1137
near_boundary_preferred_snapshots: 39
candidate_pairs: 2386
candidate_rows: 7158
actor_parameters_changed: false
ppo_used: false
promoted: false
```

M987 is negative. Increasing continuation horizon to 20 does not expose
wrong-history collisions or accepted margin gaps.

## Window Coverage

| Surface | Already failed | Near-cliff preferred | Early safe |
| --- | ---: | ---: | ---: |
| brake_loss | 130 | 9 | 106 |
| heavy_cg_delay | 133 | 20 | 112 |
| high_speed_close | 138 | 0 | 3 |
| lateral_loss | 168 | 0 | 70 |
| low_mu | 198 | 10 | 40 |

Longer continuation changes which snapshots remain normal-success near-cliff:
`lateral_loss` and `high_speed_close` no longer contribute near-cliff preferred
rows under this horizon.

## Candidate Outcome

```text
candidate_normal_success_rate: 1.0
candidate_wrong_success_rate: 1.0
candidate_wrong_first_action_threshold_rows: 7158
candidate_wrong_sequence_threshold_rows: 7137
candidate_preferred_rejected_threshold_rows: 7090
candidate_all_action_threshold_rows: 7090
candidate_margin_threshold_rows: 0
candidate_max_margin_gap: 0.002010
```

Top margin-gap row:

```text
surface: heavy_cg_delay
target: unavoidable
left_seed/right_seed: 98789/98744
left_step/right_step: 30/24
normal_margin: 0.157313
wrong_margin: 0.155303
margin_gap: 0.002010
preferred_vs_rejected_action_mean_l2: 0.163475
terminal reason: continuation_limit / continuation_limit
```

Several brake-loss rows complete the obstacle under both normal and wrong
history. Wrong-history actions remain different, but not damaging enough.

## Interpretation

Supported:

```text
Longer continuation horizon is not the missing ingredient for these mined rows.
The current wrong-matched-history intervention mostly changes actions without producing outcome degradation.
The existing global extreme scenario configs still do not yield a source-diverse proof surface.
```

Not supported:

```text
M986 was negative only because max_continuation_steps=9 was too short.
The current scenario-family branch should proceed to training or PPO.
```

Failure taxonomy:

```text
scenario_sampling_failure
```

## Decision

Do not train. Do not lower thresholds. Do not run PPO.

Route to synthesis:

```text
m988-v4-public-base-extreme-scenario-family-synthesis
```

The branch should pivot away from same-config mining and toward explicit
capability-step/fault simulation design. The current single-track model can
represent global hidden capability changes, but not per-wheel faults without a
dynamics extension.

## Artifacts

```text
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/summary.json
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/snapshot_bank_summary.csv
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/normal_window_summary.csv
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/candidate_scores.csv
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/normal_success_boundary_rows.csv
runs/m987_v4_public_base_extreme_near_cliff_long_horizon_audit/normal_success_boundary_corpus.npz
```
