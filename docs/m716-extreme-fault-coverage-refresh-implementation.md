# M716 Extreme-Fault Coverage Refresh Implementation

## Purpose

M716 runs the full no-training v2 extreme-fault coverage wave designed in M715.
The question is whether broader hidden fault coverage reveals matched-history
cases where wrong cross-fault history changes the deployed action or outcome.

This milestone is diagnostic-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.extreme_dynamics_scenario_corpus \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --config configs/extreme_fault_coverage_v2_scenarios.json \
  --pairing-mode cross_fault \
  --seed-start 72000 \
  --seed-count 512 \
  --device cpu \
  --run-dir runs/m716_extreme_fault_coverage_refresh
```

## Artifacts

```text
runs/m716_extreme_fault_coverage_refresh/summary.json
runs/m716_extreme_fault_coverage_refresh/scenario_summary.csv
runs/m716_extreme_fault_coverage_refresh/snapshot_candidates.csv
runs/m716_extreme_fault_coverage_refresh/matched_cross_fault_pairs.csv
runs/m716_extreme_fault_coverage_refresh/intervention_rollouts.csv
runs/m716_extreme_fault_coverage_refresh/accepted_rows.csv
runs/m716_extreme_fault_coverage_refresh/reset_only_rows.csv
runs/m716_extreme_fault_coverage_refresh/rejected_rows.csv
runs/m716_extreme_fault_coverage_refresh/fault_family_pair_summary.csv
runs/m716_extreme_fault_coverage_refresh/severity_pair_summary.csv
runs/m716_extreme_fault_coverage_refresh/model_fidelity_limits.md
```

## Result Summary

```text
result_class: cross_fault_reset_only

seed_count:                 512
fault_count:                 32
future_only_fault_count:     10
scenario_count:           16896
snapshot_count:           72056
matched_pair_count:        4096
unmatched_rows:              12

accepted_rows:               0
reset_only_rows:            58
rejected_rows:            4038
normal_failed_rejected:    926
history_insensitive_rejected: 3112

history_action_critical_rows:        58
wrong_history_action_critical_rows:   0
reset_history_action_critical_rows:  58

actor_parameters_changed: false
training_started: false
ppo_used: false
promoted: false
```

M716 increases reset-history evidence relative to M707:

```text
M707 reset_only_rows: 15 / 2048 pairs
M716 reset_only_rows: 58 / 4096 pairs
```

But it does not create the stronger wrong-history evidence:

```text
M707 wrong_history_action_critical_rows: 0
M716 wrong_history_action_critical_rows: 0
```

## Gap Diagnostics

Across all `4096` matched pairs:

```text
wrong action_l2_gap:
  mean: 0.001505
  p90:  0.003235
  p99:  0.008166
  max:  0.012664

reset action_l2_gap:
  mean: 0.019987
  p90:  0.023666
  p99:  0.029606
  max:  0.033975

wrong history_margin_gap:
  mean: -0.00000109
  p99:   0.00013356
  max:   0.00065534

reset margin_gap:
  mean: 0.001244
  p99:  0.023108
  max:  0.065910
```

The action threshold is `0.015`, so wrong-history action gaps remain below the
acceptance threshold even in the broadened v2 corpus. Reset-hidden gaps are
large enough to produce reset-only rows.

## Reset-Only Concentration

Top reset-only fault-family pairs:

```text
front_lateral_authority_drop -> steering_fault:         13
combined_fault -> front_lateral_authority_drop:         11
front_lateral_authority_drop -> combined_fault:         10
steering_fault -> front_lateral_authority_drop:          8
drive_authority_drop -> drive_authority_drop:            4
mass_cg_shift -> brake_authority_drop:                   4
```

Top preferred fault families in reset-only rows:

```text
front_lateral_authority_drop: 23
combined_fault:              13
steering_fault:               8
drive_authority_drop:         5
mass_cg_shift:                4
global_mu_drop:               3
brake_authority_drop:         2
```

Top preferred faults:

```text
front_puncture_proxy_severe:          10
puncture_brake_proxy:                  7
front_puncture_proxy_moderate:         7
front_puncture_proxy_extreme_surprise: 6
front_brake_combo:                     6
```

This reinforces that front-authority / puncture-proxy / steering and combined
faults are the most useful current-model stressors, but they still mostly show
reset-hidden sensitivity rather than wrong-history misidentification.

## Interpretation

M716 partially supports the user's coverage concern:

```text
broader extreme-fault coverage produces more reset-history-sensitive rows.
```

But it does not support the stronger claim:

```text
the lack of wrong-history evidence was only because M704/M707 had too little
current-model fault coverage.
```

Within the current single-track fault/proxy boundary, merely adding more
families, severities, and surprise activations still leaves wrong-history
interventions action-washed-out.

## Supported Claims

M716 supports:

```text
1. The v2 coverage runner is executable and writes the expected full data wave.

2. Extreme hidden-condition coverage increases reset-history sensitivity.

3. Front lateral authority / puncture proxies, steering faults, and combined
   faults remain the most productive current-model stressors.

4. The actor recurrent state matters under some v2 fault rows, because reset
   hidden can degrade action and margin.
```

## Falsified Claims

M716 falsifies:

```text
1. Current-model/proxy fault coverage expansion alone is enough to produce
   source-positive wrong-history self-ID evidence.

2. M704/M707 were negative only because their fault list was too small.

3. The current v2 single-track proxy corpus can support immediate source export,
   actor update, PPO, or promotion.
```

M716 does not falsify:

```text
1. True wheel-asymmetric physics may produce stronger evidence after a four-wheel
   or explicit yaw-disturbance model exists.

2. Delayed-history or action-response mismatch interventions may be more
   diagnostic than cross-fault hidden injection alone.

3. M713 actor-head residual/objective design may still be useful for turning
   existing feature-level signal into action-level signal.
```

## Failure Taxonomy

Primary:

```text
scenario_sampling_failure
```

Reason:

```text
The broader v2 current-model/proxy scenario sampling produced reset-only rows
but no wrong-history action-critical rows.
```

Secondary caution:

```text
metric_artifact
```

Reason:

```text
Reset-hidden gaps are large, but wrong-history gaps remain below action and
margin thresholds; reset sensitivity alone should not be reported as matched
wrong-history self-identification.
```

Not classified as:

```text
training_instability:
  no training occurred.

contract_violation:
  actor observations were unchanged.

proof_washout:
  actor parameters were unchanged.
```

## Next Step

M717 should audit this result before any further generator work.

The audit should decide between:

```text
1. delayed-history / action-response-mismatch intervention design
2. four-wheel or explicit yaw-disturbance dynamics design
3. returning to M713 actor-head residual/objective design using v2 rows
```

Do not continue by simply adding another small set of current-model proxy
faults. The v2 wave was large enough to show that current-model coverage
expansion alone is not producing wrong-history source-positive evidence.
