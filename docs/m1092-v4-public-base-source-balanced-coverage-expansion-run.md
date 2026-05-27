# M1092 V4 Public Base Source-Balanced Coverage Expansion Run

## Purpose

M1092 tests whether M1091's failed proof surface was only short on selected
candidate coverage. It increases the source-balanced relocation candidate
budget from `512` to `1024` and raises the per checkpoint-target cap from `64`
to `128`.

This milestone does not train, run PPO, promote a checkpoint, use private
holdout, change actor inputs, or weaken robustness thresholds.

## Command Result

The pre-registered command completed successfully:

```text
manifest: m1092-v4-public-base-source-balanced-coverage-expansion-run
commands: 1
failed: 0
elapsed_seconds: 2067.951
run_dir: runs/m1092_source_balanced_coverage_expansion_seed109200
receipt: runs/m1092_manifest_receipt/run_receipt.json
```

## Source Budget

The source budget remains ready:

```text
candidate_wrong_history_rows: 7257
eligible_physical_pairs: 371
eligible_left_steps: 28
eligible_checkpoints: 4
eligible_targets: 3
max_candidate_pair_fraction: 0.004409535620779937
source_budget_ready: true
```

The expanded selected candidate set remained source-balanced:

```text
selected_rows: 1024
selected_physical_pairs: 371
selected_left_steps: 28
selected_targets: 3
max_selected_rows_per_physical_pair: 5
max_selected_pair_fraction: 0.0048828125
decision: source_balanced_candidates_ready
```

## Robustness Result

M1092 passes the unchanged source-diverse wrong-history robustness gate:

```text
decision: source_balanced_boundary_export_pass
passed: true
relocation_replay_started: true
```

Gate table:

```text
accepted_wrong_rows: 146 / 80 required -> pass
accepted_wrong_physical_pairs: 18 / 10 required -> pass
accepted_wrong_left_steps: 9 / 5 required -> pass
accepted_wrong_checkpoints: 4 / 3 required -> pass
accepted_wrong_targets: 3 / 2 required -> pass
accepted_wrong_normal_margin_buckets: 4 / 2 required -> pass
accepted_wrong_success_drop_fraction: 1.0 / 1.0 required -> pass
max_rows_per_physical_pair_fraction: 0.1369863014 <= 0.25 -> pass
control_accepted_wrong_rows: 0 <= 0 -> pass
```

This confirms the M1091 failure was a candidate-coverage shortfall, not a
source-budget, duplicate-dominance, success-drop, or control-row failure.

## Distribution Notes

Accepted rows by checkpoint/target:

```text
short61051 / future_yaw_response: 33
short61049 / future_yaw_response: 27
proof_current / future_yaw_response: 21
short61051 / future_braking_deceleration: 19
proof_current / future_braking_deceleration: 18
short61050 / future_braking_deceleration: 17
short61050 / future_yaw_response: 4
short61050 / future_lateral_accel_response: 3
short61049 / future_braking_deceleration: 2
short61051 / future_lateral_accel_response: 2
```

Accepted margins:

```text
normal_margin_min: 0.000171
normal_margin_mean: 0.003514
normal_margin_max: 0.016103
margin_gap_mean: 0.006183
margin_gap_max: 0.023191
```

The largest physical pair contributes `20 / 146` accepted rows, still below
the `0.25` dominance cap.

## Self-ID Claim Level

M1092 supports a source-balanced level-2 wrong-history proof-surface result:

```text
level2_history_encoded_reactive proof-surface evidence:
  admitted for compact corpus conversion
```

It does not support level-3 anticipatory self-identification. The task still
uses matched-current snapshots and current ego response; no pre-emergency
warm-up evidence window was added.

## Decision

```text
source_balanced_coverage_expansion_pass_route_to_compact_conversion_design
```

Next:

```text
m1093-v4-public-base-source-balanced-compact-corpus-conversion-design
```

M1093 should design compact conversion from:

```text
runs/m1092_source_balanced_coverage_expansion_seed109200/balanced_accepted_wrong_history_rows.csv
```

The conversion must preserve source caps, run objective sanity and replay
sanity before any future PPO, and continue to forbid promotion or private
holdout use.
