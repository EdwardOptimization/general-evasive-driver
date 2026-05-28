# M1333 Paper-Route Source Top-Up Materialization Implementation

## Summary

M1333 implemented and ran the source-topup response-history materializer for the
M1330/M1331 merged source corpus.

Decision:

```text
source_topup_response_history_materialization_pass_route_to_result_audit
```

The structural materialization gates pass:

```text
source_pair_rows: 366
history_prefix_rows: 1464
history_frame_rows: 35136
history_intervention_rows: 1464
wrong_history_pair_rows: 1464
scenario_lookup_missing_count: 0
fault_lookup_missing_count: 0
source_identity_duplicate_count: 0
wrong_history_valid_count: 1464
actor_view_history_all_finite: true
forbidden_actor_view_history_columns: []
```

This is infrastructure progress only. It is not driver performance, not PPO,
not checkpoint promotion, and not a self-identification claim.

## Implementation

Added:

```text
src/autodrift/source_topup_response_history_materialization.py
tests/test_source_topup_response_history_materialization.py
```

The materializer is dedicated to the merged source-topup corpus. It does not
reuse M1280 directly because M1280 assumes the early default fault profile, lacks
source-run identity semantics, and does not apply newer fault `params_override`
values.

Source dispatch:

```text
source_run_id=m1322_source_repair_corpus_export
  source_run_dir=runs/m1320_inactive_source_family_repair_smoke
  fault_profile=source_repair_v1

source_run_id=m1327_source_repair_topup_horizon_corrected_smoke
  source_run_dir=runs/m1327_source_repair_topup_horizon_corrected_smoke
  fault_profile=source_topup_v1
```

Preserved identity columns:

```text
source_run_id
source_row_id
original_pair_id
source_identity
```

## Commands

Focused test:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_source_topup_response_history_materialization.py
```

Result:

```text
1 passed in 2.11s
```

Materialization:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.source_topup_response_history_materialization \
  --merged-source-run-dir runs/m1330_source_topup_additive_merge_export \
  --expansion-plan-run-dir runs/m1331_source_topup_merged_corpus_expansion_plan \
  --base-source-run-dir runs/m1320_inactive_source_family_repair_smoke \
  --topup-source-run-dir runs/m1327_source_repair_topup_horizon_corrected_smoke \
  --run-dir runs/m1333_source_topup_response_history_materialization \
  --history-length 24 \
  --dt 0.02
```

## Artifacts

Primary artifacts:

```text
runs/m1333_source_topup_response_history_materialization/summary.json
runs/m1333_source_topup_response_history_materialization/source_pair_rows.csv
runs/m1333_source_topup_response_history_materialization/history_prefix_rows.csv
runs/m1333_source_topup_response_history_materialization/history_frame_rows.csv
runs/m1333_source_topup_response_history_materialization/history_intervention_rows.csv
runs/m1333_source_topup_response_history_materialization/wrong_history_pair_rows.csv
runs/m1333_source_topup_response_history_materialization/source_lineage_rows.csv
runs/m1333_source_topup_response_history_materialization/materialization_limits.md
```

## Result

Summary:

```text
result_class: source_topup_response_history_materialization_pass
expected_source_pairs: 366
expected_pair_probe_groups: 732
expected_history_prefix_rows: 1464
expected_history_frame_rows: 35136
source_pair_rows: 366
history_prefix_rows: 1464
history_frame_rows: 35136
history_intervention_rows: 1464
wrong_history_pair_rows: 1464
```

Lookup and identity:

```text
scenario_lookup_missing_count: 0
fault_lookup_missing_count: 0
plan_lookup_missing_count: 0
source_identity_duplicate_count: 0
source_identity_metadata_preserved: true
wrong_history_valid_count: 1464
```

Actor-view history:

```text
actor_view_history_column_count: 12
actor_view_history_all_finite: true
forbidden_actor_view_history_columns: []
```

Actor-view history columns:

```text
vx
vy
yaw_rate
ax
ay
steer_state
steer_rate
drive_state
brake_state
prev_cmd_steer
prev_cmd_throttle
prev_cmd_brake
```

The frame CSV also contains metadata and probe command columns for audit and
projection. Those columns are not actor-view inputs.

## Family Coverage

History prefix counts by source family:

```text
steering_actuator_fault: 384
single_wheel_grip_collapse: 256
single_wheel_brake_pull: 248
load_cg_perturbation: 216
left_right_split_mu: 148
tire_blowout_like: 124
halfshaft_torque_loss: 88
```

Prefix counts by source run:

```text
m1322_source_repair_corpus_export: 864
m1327_source_repair_topup_horizon_corrected_smoke: 600
```

Global friction remains absent and halfshaft remains below the 30-row source
target:

```text
global_friction_missing: true
halfshaft_undercovered: true
```

## Distinguishability Diagnostics

Response diagnostics:

```text
response_l2_mean: 0.3003082731
response_l2_min: 0.0
response_l2_ge_0_01_count: 1376 / 1464
final_yaw_rate_diff_ge_0_01_count: 1300 / 1464
final_vy_diff_ge_0_01_count: 1280 / 1464
```

Important diagnostic:

```text
zero response_l2 prefixes: 88
zero response_l2 family: halfshaft_torque_loss, 88 / 88
```

Interpretation:

```text
The materializer is structurally valid, but the current left/right brake probes
do not excite halfshaft torque-loss differences. This is expected because those
probes use throttle -1.0 and brake +1.0, so drive-side asymmetry is largely
silent.
```

This does not invalidate the materialization pass because M1333 did not require
every family to be history-distinguishable. It does block blindly treating the
full corpus as equally useful for source-history objective training.

## Guardrails

Guardrails held:

```text
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
accepted_thresholds_relaxed: false
high_fidelity_validation_claimed: false
```

## Interpretation

Supported:

```text
The M1330/M1331 merged source corpus can be materialized into clean
source-identity-preserving command-response history artifacts.
```

Supported:

```text
Source-run-specific fault profiles and params_override values are necessary and
now handled by the materializer.
```

Still unsupported:

```text
halfshaft response-history distinguishability under the current brake probes;
global friction source coverage;
policy-side source-history objective improvement;
closed-loop PPO continuation;
promotion;
paper-level evidence;
strong self-identification.
```

## Decision

Do not train.

Do not run PPO.

Do not promote.

Do not integrate into actor/Gym yet.

Admit one result audit and branch synthesis:

```text
m1334-paper-route-source-topup-materialization-result-audit
```

M1334 should decide whether to:

```text
1. use the materialized corpus minus halfshaft for the next source-history
   objective route;
2. add drive-sensitive halfshaft history probes before objective tuning;
3. synthesize and close the top-up branch before opening the next branch.
```
