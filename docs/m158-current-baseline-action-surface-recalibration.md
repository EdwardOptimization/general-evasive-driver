# M158 Current-Baseline Action Surface Recalibration

Date: 2026-05-22

## Question

M157 rejected the M156 full M154 repeat because the matched-history action gate
returned zero intervention rows. M158 checks whether that means M156 lost
wrong-history action dependence, or whether the gate surface was not calibrated
for the current M142/M156 guarded baseline family.

## Harness Finding

The M157 zero-row result was a harness surface-binding problem.

`matched_history_intervention_gate` previously selected only rows whose
`pairs_csv.checkpoint_label` matched the evaluated checkpoint label. The M118
matched-pair corpus was mined under source labels:

```text
m62
m102
m105
```

Current checkpoints use labels such as:

```text
m142_a400
m156_s20
```

Therefore the gate selected no pairs for current checkpoint labels. M158 adds a
non-default mode:

```text
--pair-label-mode all
```

In this mode the gate preserves the original pair label as
`source_checkpoint_label`, relabels `checkpoint_label` to the current evaluated
checkpoint, and keeps the default historical behavior under
`--pair-label-mode matching`.

## Old M24 Surface Recheck

M158 first confirmed the diagnosis with a label-hack calibration and then with
the new `pair-label-mode=all`.

Run:

```text
runs/m158_pair_all_m24_m156_seed9510
```

Input:

```text
pairs_csv:  runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv
env_config: configs/ppo_m24_human_view_gru_driver.json
checkpoint: runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt
```

Wrong-history action aggregate:

| Metric | Value |
| --- | ---: |
| wrong rows | 408 |
| physical pairs | 295 |
| mean action distance | 0.072531 |
| above `0.02` fraction | 0.830882 |
| closer-to-right fraction | 0.762255 |

The source labels are preserved:

| source label | wrong rows |
| --- | ---: |
| m62 | 136 |
| m102 | 138 |
| m105 | 134 |

This proves the old zero-row failure was not absence of an action signal for the
M156 checkpoint.

## Zero-Relvel Surface Compatibility

The old M118 surface cannot be directly reused under the current
zero-obstacle-relative-velocity profile. Attempts to replay M118 pairs with
`configs/m121_human_view_zero_obstacle_relvel.json` failed while reconstructing
snapshots. The old pair steps were generated under the older M24 rollout
surface, so the current zero-relvel profile needs a fresh matched-current
surface.

## Current Zero-Relvel Corpus

M158 mined a fresh current-baseline corpus:

```text
runs/m158_current_baseline_matched_current_zero_relvel_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 9510,9511 \
  --episodes 30 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 800 \
  --nearest-k 10 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 200 \
  --max-pairs-per-physical-pair 1 \
  --min-accepted-pairs 30 \
  --device cpu \
  --run-dir runs/m158_current_baseline_matched_current_zero_relvel_seed9510
```

Corpus summary:

| Metric | Value |
| --- | ---: |
| candidate pairs | 56310 |
| accepted pairs | 318 |
| accepted physical pairs | 94 |
| max rows per physical pair | 4 |

Accepted targets:

| Target | Accepted pairs |
| --- | ---: |
| future braking deceleration | 132 |
| future lateral accel response | 102 |
| future yaw response | 84 |

## Current Zero-Relvel Action Gate

Run:

```text
runs/m158_current_baseline_action_gate_zero_relvel_seed9510
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m142_a400=runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt \
  --checkpoint-policy m156_s20=runs/m156_capability_belief_aux_s20_seed9630/optimized_checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m158_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --device cpu \
  --run-dir runs/m158_current_baseline_action_gate_zero_relvel_seed9510
```

Summary:

| Metric | Value |
| --- | ---: |
| input pairs | 318 |
| intervention rows | 1590 |
| variant summary rows | 30 |

Wrong-history aggregate:

| Scope | Wrong rows | Physical pairs | Mean action distance | Above `0.02` | Closer-to-right |
| --- | ---: | ---: | ---: | ---: | ---: |
| all | 318 | 176 | 0.046298 | 0.761006 | 0.858491 |
| m142_a400 | 160 | 89 | 0.045232 | 0.731250 | 0.868750 |
| m156_s20 | 158 | 87 | 0.047378 | 0.791139 | 0.848101 |

Per-target wrong-history rows:

| Checkpoint | Braking | Lateral | Yaw |
| --- | ---: | ---: | ---: |
| m142_a400 | 67 | 50 | 43 |
| m156_s20 | 65 | 52 | 41 |

## Interpretation

M158 is positive as a recalibration milestone:

- the action-gate harness now separates source labels from evaluated checkpoint
  labels;
- M156 has broad wrong-history action dependence on the old M24 surface once
  label binding is removed;
- a fresh current zero-relvel surface exists for the M142/M156 family;
- M156 is not uniquely worse than M142 on that surface.

M158 does not admit PPO or strict proof-surface work yet. The current
zero-relvel corpus clears the action-distance and closer-to-right thresholds,
but per-checkpoint physical-pair coverage is still below the M154 target of
`100`:

```text
m142_a400: 89 physical pairs
m156_s20: 87 physical pairs
```

The combined surface has enough physical pairs, but the next gate should broaden
the current zero-relvel corpus until each evaluated checkpoint has enough
coverage, then repeat the M154 matched-history action stage before returning to
outcome gates or PPO.

## Decision

Complete M158 as a positive harness and calibration milestone.

Next task: M159 should broaden the current zero-relvel current-baseline
matched-pair corpus and rerun the action stage with the registered M154
thresholds. Do not start PPO from M156 until that repeat passes.
