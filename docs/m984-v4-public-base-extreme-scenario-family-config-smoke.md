# M984 V4 Public Base Extreme Scenario Family Config Smoke

## Purpose

M984 starts the new `v4_public_base_extreme_scenario_family_generation` branch.
It creates richer hidden-dynamics scenario-family configs and runs a small
no-PPO smoke through the existing source miner.

Current public-gate base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

M984 does not train, run PPO, promote, use private holdout, or change actor
inputs. The configs change only simulator/task distributions.

## Created Configs

```text
configs/m984_extreme_low_mu_drop.json
configs/m984_brake_authority_loss.json
configs/m984_lateral_authority_loss.json
configs/m984_heavy_cg_delay.json
configs/m984_high_speed_close_obstacle.json
```

Supported by the current single-track simulator:

```text
global low-friction / friction-step events
global brake authority loss
global lateral tire stiffness loss
global drive authority variation
mass / inertia / CG shift
steering and drive actuator lag
high-speed close-obstacle emergency geometry
```

Not claimed by M984:

```text
split-mu
single tire puncture
half-shaft breakage
corner-specific brake loss
individual wheel failures
```

Those require a future dynamics extension rather than config-only coverage.

## Smoke Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.normal_success_boundary_source_miner \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --surface-config low_mu=configs/m984_extreme_low_mu_drop.json \
  --surface-config brake_loss=configs/m984_brake_authority_loss.json \
  --surface-config lateral_loss=configs/m984_lateral_authority_loss.json \
  --surface-config heavy_cg_delay=configs/m984_heavy_cg_delay.json \
  --surface-config high_speed_close=configs/m984_high_speed_close_obstacle.json \
  --surface-seed-range low_mu=98400:98415 \
  --surface-seed-range brake_loss=98420:98435 \
  --surface-seed-range lateral_loss=98440:98455 \
  --surface-seed-range heavy_cg_delay=98460:98475 \
  --surface-seed-range high_speed_close=98480:98495 \
  --sequence-lengths 5 \
  --obstacle-distance-min 0.0 \
  --obstacle-distance-max 35.0 \
  --normal-margin-min 0.0 \
  --normal-margin-max 1.0 \
  --max-right-candidates-per-left 32 \
  --max-candidate-pairs-per-surface 120 \
  --context-distance-threshold 0.25 \
  --response-distance-threshold 0.20 \
  --obstacle-x-abs-delta 10.0 \
  --obstacle-y-abs-delta 2.0 \
  --step-abs-delta 30 \
  --min-wrong-first-action-l2 0.002 \
  --min-wrong-action-sequence-mean-l2 0.006 \
  --min-preferred-rejected-action-mean-l2 0.010 \
  --min-margin-gap 0.010 \
  --max-snapshots-per-surface 80 \
  --max-snapshots-per-seed 4 \
  --sample-stride 4 \
  --max-continuation-steps 7 \
  --device auto \
  --run-dir runs/m984_v4_public_base_extreme_scenario_family_config_smoke
```

## Result

```text
corpus_passed: false
accepted_rows: 0
snapshot_count: 211
near_boundary_preferred_snapshots: 57
candidate_pairs: 534
candidate_rows: 534
candidate_normal_success_rate: 1.0
candidate_wrong_success_rate: 1.0
actor_parameters_changed: false
ppo_used: false
promoted: false
```

The smoke passes as an infrastructure/config milestone. `accepted_rows=0` is
not a failure here because M984 is not the full mining run.

## Family Coverage

Snapshot summary:

| Surface | Snapshots | Seeds | Targets | Obstacle distance mean |
| --- | ---: | ---: | ---: | ---: |
| brake_loss | 50 | 16 | 2 | 2.793653 |
| heavy_cg_delay | 52 | 16 | 3 | 3.074152 |
| high_speed_close | 30 | 16 | 1 | 3.341877 |
| lateral_loss | 39 | 16 | 2 | 3.184080 |
| low_mu | 40 | 16 | 2 | 3.342420 |

Normal-window summary:

| Surface | Already failed | Near-boundary preferred | Early safe |
| --- | ---: | ---: | ---: |
| brake_loss | 15 | 24 | 11 |
| heavy_cg_delay | 14 | 12 | 26 |
| high_speed_close | 28 | 2 | 0 |
| lateral_loss | 26 | 11 | 2 |
| low_mu | 30 | 8 | 2 |

All five families can sample valid obstacle scenarios and produce artifacts.
`high_speed_close` is intentionally harsh and mostly already-failed in this
small smoke, so full mining should treat it as a stress family rather than a
guaranteed source of near-boundary rows.

## Candidate Outcome

```text
candidate_wrong_first_action_threshold_rows: 533
candidate_wrong_sequence_threshold_rows: 515
candidate_preferred_rejected_threshold_rows: 468
candidate_all_action_threshold_rows: 468
candidate_margin_threshold_rows: 0
candidate_max_margin_gap: 0.000373
```

Action separation is live in the smoke, but wrong-history continuations remain
successful. This is acceptable for M984 and motivates a larger M985 source
mining run.

## Decision

M984 admits multi-family source mining.

Next:

```text
m985-v4-public-base-extreme-scenario-family-source-mining
```

M985 should keep PPO/training/promotion blocked and use the five M984 configs
with larger seed and candidate coverage to test whether richer scenario
families expose source-diverse outcome-sensitive wrong-history rows.

## Artifacts

```text
configs/m984_extreme_low_mu_drop.json
configs/m984_brake_authority_loss.json
configs/m984_lateral_authority_loss.json
configs/m984_heavy_cg_delay.json
configs/m984_high_speed_close_obstacle.json
runs/m984_v4_public_base_extreme_scenario_family_config_smoke/summary.json
runs/m984_v4_public_base_extreme_scenario_family_config_smoke/snapshot_bank_summary.csv
runs/m984_v4_public_base_extreme_scenario_family_config_smoke/normal_window_summary.csv
runs/m984_v4_public_base_extreme_scenario_family_config_smoke/candidate_scores.csv
```
