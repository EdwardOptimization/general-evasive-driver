# M1091 V4 Public Base Source-Balanced Boundary Relocation Run

## Purpose

M1091 runs the first full source-balanced boundary relocation replay using the
M1090 runner. This is a proof-surface evaluation only. It does not train, run
PPO, promote a checkpoint, use private holdout, or weaken robustness
thresholds.

## Command Result

The pre-registered command completed successfully:

```text
manifest: m1091-v4-public-base-source-balanced-boundary-relocation-run
commands: 1
failed: 0
elapsed_seconds: 1037.385
run_dir: runs/m1091_source_balanced_boundary_relocation_seed109100
receipt: runs/m1091_manifest_receipt/run_receipt.json
```

The run used the M1090 source-balanced full relocation path, not the old
source-unaware relocation runner.

## Source Budget

The pre-boundary source budget passed:

```text
candidate_wrong_history_rows: 7257
eligible_physical_pairs: 371
eligible_left_steps: 28
eligible_checkpoints: 4
eligible_targets: 3
max_candidate_pair_fraction: 0.004409535620779937
source_budget_ready: true
```

The selected relocation candidate set was also source-balanced:

```text
selected_rows: 512
selected_physical_pairs: 370
selected_left_steps: 28
selected_targets: 3
max_selected_rows_per_physical_pair: 3
max_selected_pair_fraction: 0.005859375
decision: source_balanced_candidates_ready
```

This confirms the M1088/M1089/M1090 premise: the source budget exists before
relocation, and balanced candidates can enter replay.

## Robustness Result

The boundary export did not pass the unchanged robustness gate:

```text
decision: reject_boundary_wrong_history_surface
passed: false
relocation_replay_started: true
```

Gate table:

```text
accepted_wrong_rows: 76 / 80 required -> fail
accepted_wrong_physical_pairs: 18 / 10 required -> pass
accepted_wrong_left_steps: 9 / 5 required -> pass
accepted_wrong_checkpoints: 4 / 3 required -> pass
accepted_wrong_targets: 3 / 2 required -> pass
accepted_wrong_normal_margin_buckets: 4 / 2 required -> pass
accepted_wrong_success_drop_fraction: 1.0 / 1.0 required -> pass
max_rows_per_physical_pair_fraction: 0.1578947368 <= 0.25 -> pass
control_accepted_wrong_rows: 0 <= 0 -> pass
```

The old blocker is fixed: this is no longer a six-physical-pair duplicate
surface. The new blocker is a near-threshold accepted-row-count shortfall. The
run misses by four accepted wrong-history rows while all source-diversity,
success-drop, bucket, dominance, and control gates pass.

## Distribution Notes

Accepted rows are source-diverse:

```text
accepted_wrong_physical_pairs: 18
accepted_wrong_left_steps: 9
accepted_wrong_checkpoints: 4
accepted_wrong_targets: 3
max_rows_per_physical_pair: 12
```

Accepted rows by strongest checkpoint/target groups:

```text
proof_current / future_yaw_response: 14
short61051 / future_braking_deceleration: 13
short61049 / future_yaw_response: 13
short61051 / future_yaw_response: 12
proof_current / future_braking_deceleration: 9
short61050 / future_braking_deceleration: 9
```

The selected candidate set hit the `64` per checkpoint-target cap for several
active groups. Since the run only needed four additional accepted rows, the
next step should increase coverage before replay while preserving all
robustness thresholds.

## Self-ID Claim Level

M1091 supports only this claim:

```text
level2_history_encoded_reactive proof-surface evidence remains plausible but
not admitted by this run because the accepted-row threshold failed.
```

It does not support a level3 anticipatory self-identification claim. The run
does not add a pre-emergency warm-up window and still allows current-frame ego
response, so current-frame substitution risk remains documented.

## Decision

```text
source_balanced_relocation_row_count_shortfall_route_to_coverage_expansion
```

Next:

```text
m1092-v4-public-base-source-balanced-coverage-expansion-run
```

M1092 should increase source-balanced candidate coverage before replay, for
example `max_candidates=1024` and a larger per checkpoint-target cap, while
keeping the same robustness thresholds and no training/PPO/promotion/private
holdout constraints.
