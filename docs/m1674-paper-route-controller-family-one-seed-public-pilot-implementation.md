# M1674 Paper-Route Controller-Family One-Seed Public Pilot Implementation

## Summary

M1674 runs the one-seed public standard-layer plumbing pilot designed by M1673.

Decision:

```text
one_seed_public_pilot_completed_route_to_result_audit
```

This milestone runs the pre-registered one-seed public PPO train/eval pilot for
all 12 corrected controller-family profiles. It does not use private holdout,
promote checkpoints, change actor inputs, repair the M1663 artifact, execute a
decisive clean-package benchmark, or claim controller-family ranking,
paper-level evidence, or level3 self-identification.

## Command

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --training-seed-base 167400 \
  --seed-offsets 0 \
  --eval-seed-base 167500 \
  --eval-episodes 64 \
  --device cpu
```

## Artifacts

```text
runs/m1674_controller_family_one_seed_public_pilot/summary.json
runs/m1674_controller_family_one_seed_public_pilot/protocol.json
runs/m1674_controller_family_one_seed_public_pilot/profile_seed_rows.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_aggregate.csv
runs/m1674_controller_family_one_seed_public_pilot/eval_rows.csv
```

## Gate Result

M1674 passed its plumbing gates:

```text
result_class: corrected_profile_pilot_completed
profile_count: 12
total_seed_runs: 12
completed_seed_runs: 12
failed_seed_runs: 0
all_selected_profile_seed_runs_complete: true
all_eval_metrics_finite: true
private_holdout_used: false
profile_specific_tuning: false
actor_input_contract_changed: false
promoted: false
self_identification_claimed: false
paper_level_claimed: false
runtime_seconds: 89.94460060913116
```

## Aggregate Metrics

One-seed public aggregate:

| Profile | Success | Collision | Mean Margin |
| --- | ---: | ---: | ---: |
| L0_current_masked | 0.156250 | 0.843750 | 0.020294 |
| L1_one_step | 0.234375 | 0.765625 | 0.083796 |
| L2_window_13 | 0.250000 | 0.328125 | 1.186575 |
| L2_window_13_current_tiled | 0.250000 | 0.328125 | 1.164752 |
| L2_window_25 | 0.250000 | 0.328125 | 1.186577 |
| L2_window_25_current_tiled | 0.250000 | 0.328125 | 1.164361 |
| L2_window_50 | 0.250000 | 0.328125 | 1.186577 |
| L2_window_50_current_tiled | 0.250000 | 0.328125 | 1.164362 |
| L2_window_100 | 0.250000 | 0.328125 | 1.186577 |
| L2_window_100_current_tiled | 0.250000 | 0.328125 | 1.164362 |
| L3_online_gru | 0.296875 | 0.703125 | 0.118231 |
| L3_reset_control_corrected | 0.343750 | 0.656250 | 0.162992 |

Diagnostic observations for the audit:

```text
L2 normal and current-tiled have identical success/collision on this one seed;
L2 normal has only about 0.022 mean-margin advantage over current-tiled;
L3 reset-control outperforms L3 online on success, collision, and mean margin;
L2 family has lower collision and higher mean margin than L1/L3 on this seed;
one seed is not architecture ranking evidence.
```

## Supported Claims

Supported:

```text
the 12-profile corrected public pilot runner still works;
all profiles complete one public seed with finite metrics;
the run preserved no-private-holdout, no-profile-specific-tuning, no-promotion,
and no-actor-contract-change guardrails;
the result is ready for M1675 audit.
```

## Unsupported Claims

Unsupported:

```text
controller-family ranking;
finite-window history necessity;
online-GRU recurrent advantage;
decisive-history task performance;
private-holdout generalization;
checkpoint promotion;
paper-level evidence;
level3 self-identification.
```

## Decision

Route to:

```text
m1675-paper-route-controller-family-one-seed-public-pilot-result-audit
```

M1675 must audit this run before any three-seed repeat, decisive task mapping,
or architecture interpretation.

## Guardrails

```text
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
self_identification_claimed: false
paper_level_claimed: false
next: m1675-paper-route-controller-family-one-seed-public-pilot-result-audit
```
