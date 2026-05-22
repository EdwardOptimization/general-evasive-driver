# M160 Remaining M154 Outcome/Strict Repeat

Date: 2026-05-22

## Question

M159 cleared the current zero-relvel matched-history action blocker for the M156
s20 candidate. M160 checks the next required M154 stage:

```text
Does wrong matched history reduce continuation outcome enough to prove
behavior-relevant self-identification?
```

If the outcome stage fails, strict proof-surface runs are not decision-relevant
because M154 requires all stages before PPO admission.

## Candidate

```text
runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt
```

Current action surface:

```text
runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv
```

The actor input contract is still:

```text
configs/m121_human_view_zero_obstacle_relvel.json
```

## M156 Outcome Gate

Run:

```text
runs/m160_m156_outcome_gate_zero_relvel_allpairs_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 40 \
  --min-margin-gap 0.005 \
  --max-pairs-per-checkpoint-target 0 \
  --device cpu \
  --run-dir runs/m160_m156_outcome_gate_zero_relvel_allpairs_seed9510
```

Thresholds from M154:

```text
wrong_history_margin_gap_mean_min = 0.005
wrong_history_success_drop_pairs_min = 6
selected_physical_pairs_min = 6
```

M156 wrong-history aggregate:

| Metric | Value |
| --- | ---: |
| wrong rows | 928 |
| physical pairs | 318 |
| mean margin gap | 0.000284 |
| success-drop rows | 3 |
| success-drop physical pairs | 1 |
| selected rows | 67 |
| selected physical pairs | 25 |
| normal-better fraction | 0.072198 |
| normal success rate | 0.886853 |
| wrong-history success rate | 0.883621 |

By target:

| Target | Rows | Mean margin gap | Success drops | Normal better |
| --- | ---: | ---: | ---: | ---: |
| future braking deceleration | 585 | 0.000572 | 3 | 0.061538 |
| future lateral accel response | 175 | 0.000221 | 0 | 0.154286 |
| future yaw response | 168 | -0.000651 | 0 | 0.023810 |

M156 fails the outcome gate because the margin gap and success-drop count are
both too small.

## M142 Calibration

M160 then checks whether this is a M156-only regression or a surface problem by
running the same outcome gate on M142.

Run:

```text
runs/m160_m142_outcome_calibration_zero_relvel_allpairs_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --max-continuation-steps 40 \
  --min-margin-gap 0.005 \
  --max-pairs-per-checkpoint-target 0 \
  --device cpu \
  --run-dir runs/m160_m142_outcome_calibration_zero_relvel_allpairs_seed9510
```

M142 wrong-history aggregate:

| Metric | Value |
| --- | ---: |
| wrong rows | 940 |
| physical pairs | 319 |
| mean margin gap | 0.000499 |
| success-drop rows | 0 |
| success-drop physical pairs | 0 |
| selected rows | 82 |
| selected physical pairs | 29 |
| normal-better fraction | 0.087234 |
| normal success rate | 0.874468 |
| wrong-history success rate | 0.874468 |

By target:

| Target | Rows | Mean margin gap | Success drops | Normal better |
| --- | ---: | ---: | ---: | ---: |
| future braking deceleration | 612 | 0.000764 | 0 | 0.060458 |
| future lateral accel response | 167 | 0.000739 | 0 | 0.227545 |
| future yaw response | 161 | -0.000759 | 0 | 0.043478 |

M142 also fails the outcome threshold. Therefore the M160 blocker is not a
M156-only regression; it is an action-sensitive but outcome-neutral surface.

## Strict Proof-Surface Gate

M160 does not run the expensive strict proof-surface gates after the outcome
failure. That is intentional: M154 requires the outcome stage before strict
proof-surface or PPO admission. Running strict seeds after a failed outcome gate
would not change the decision.

## Decision

M160 rejects guarded PPO admission.

The useful result is narrower:

```text
M159 proves wrong-history can change actions on the current zero-relvel surface.
M160 shows those action changes still do not reliably change continuation
outcome.
```

Next task: mine a current zero-relvel outcome-critical surface, rather than
training PPO or repeating strict proof-surface seeds on the current action-only
surface.
