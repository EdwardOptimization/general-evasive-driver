# M159 Current Action Surface Coverage Repeat

Date: 2026-05-22

## Question

M158 found a current zero-relvel matched-history action surface, but the
per-checkpoint physical-pair coverage was still below the M154 action-stage
target:

```text
m142_a400: 89 physical pairs
m156_s20: 87 physical pairs
target:    100 physical pairs
```

M159 broadens the current zero-relvel corpus without changing the actor input
contract or the wrong-history action thresholds.

## Corpus Expansion

Run:

```text
runs/m159_current_baseline_matched_current_zero_relvel_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 9510,9511,9512,9513 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m159_current_baseline_matched_current_zero_relvel_seed9510
```

Compared with M158, M159 keeps the same env profile, target delta threshold,
and actor contract, but expands:

```text
probe seeds: 2 -> 4
episodes:    30 -> 40
max samples: 800 -> 1200
nearest-k:   10 -> 12
target cap:  200 -> 320
```

Corpus summary:

| Metric | M158 | M159 |
| --- | ---: | ---: |
| candidate pairs | 56310 | 184959 |
| accepted pairs | 318 | 1868 |
| accepted physical pairs | 94 | 343 |

Accepted M159 targets:

| Target | Accepted pairs |
| --- | ---: |
| future braking deceleration | 1197 |
| future lateral accel response | 342 |
| future yaw response | 329 |

## Top-80 Registered-Cap Calibration

First, M159 reran the action gate with the historical M154 command cap:

```text
runs/m159_current_baseline_action_gate_zero_relvel_seed9510
```

Command uses:

```text
--max-pairs-per-checkpoint-target 80
```

Result:

| Checkpoint | Wrong rows | Physical pairs | Mean action distance | Above `0.02` | Closer-to-right |
| --- | ---: | ---: | ---: | ---: | ---: |
| m142_a400 | 240 | 78 | 0.036792 | 0.650000 | 0.666667 |
| m156_s20 | 240 | 84 | 0.042331 | 0.687500 | 0.691667 |

This cap fails the registered action-stage thresholds. The failure is important:
sorting to the top `target_z_delta` rows per target does not preserve enough
action-sensitive physical-pair coverage on the broadened current surface.

## Full-Surface Action Gate

M159 then evaluates the complete broadened surface rather than the top-80 cap:

```text
runs/m159_current_baseline_action_gate_zero_relvel_allpairs_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 0 \
  --device cpu \
  --run-dir runs/m159_current_baseline_action_gate_zero_relvel_allpairs_seed9510
```

The thresholds are unchanged:

```text
wrong_matched_history_physical_pairs_min = 100
wrong_matched_history_above_threshold_fraction_min = 0.70
wrong_matched_history_closer_to_right_fraction_min = 0.65
```

Full-surface wrong-history aggregate:

| Checkpoint | Wrong rows | Physical pairs | Mean action distance | Above `0.02` | Closer-to-right |
| --- | ---: | ---: | ---: | ---: | ---: |
| m142_a400 | 940 | 319 | 0.044709 | 0.732979 | 0.719149 |
| m156_s20 | 928 | 318 | 0.049950 | 0.789871 | 0.730603 |

Combined:

| Metric | Value |
| --- | ---: |
| wrong rows | 1868 |
| physical pairs | 637 |
| mean action distance | 0.047312 |
| above `0.02` fraction | 0.761242 |
| closer-to-right fraction | 0.724839 |

Target diversity:

| Checkpoint | Braking | Lateral | Yaw |
| --- | ---: | ---: | ---: |
| m142_a400 | 612 | 167 | 161 |
| m156_s20 | 585 | 175 | 168 |

Seed diversity:

```text
probe seeds: 9510, 9511, 9512, 9513
left rollout seeds: 29 unique
right rollout seeds: 20 unique
```

## Interpretation

M159 passes the current zero-relvel action-stage coverage and wrong-history
action thresholds on the full broadened surface.

The top-80 cap remains a negative calibration result. It should be treated as a
compute/sampling cap that is not reliable for the current surface. The
full-surface result is not a PPO admission and not a driver promotion; it only
clears the M154 matched-history action blocker for the current M142/M156 family.

M156 is not uniquely worse than M142:

```text
M156 has slightly higher action-distance and above-threshold fraction than M142,
while both clear coverage and closer-to-right thresholds.
```

## Decision

Complete M159 as a positive action-stage coverage repeat.

Admit M156 only to the remaining M154 repeat stages:

```text
matched-history outcome gate
strict proof-surface gate
promotion boundary check
```

Do not start PPO until those remaining stages pass.
