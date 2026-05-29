# M1675 Paper-Route Controller-Family One-Seed Public Pilot Result Audit

## Summary

M1675 audits the M1674 one-seed public standard-layer controller-family pilot.

Decision:

```text
one_seed_public_pilot_audit_route_to_decisive_task_source_mapping_design
```

The pilot is a valid plumbing pass. It is not architecture ranking, not
decisive-history evidence, not private-holdout evidence, and not level3
self-identification evidence.

## Gate Audit

M1674 satisfied the pre-registered plumbing gates:

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
```

Therefore the controller-family runner and 12 corrected profile configs remain
usable.

## Result Pattern

One-seed aggregate:

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

Diagnostic deltas:

```text
L2 normal - current-tiled success delta: 0.000000 for all windows
L2 normal - current-tiled collision delta: 0.000000 for all windows
L2 normal - current-tiled mean-margin delta: about +0.0218 to +0.0222
L3 online - L3 reset success delta: -0.046875
L3 online - L3 reset collision delta: +0.046875
L3 online - L3 reset mean-margin delta: -0.044761
```

This repeats the important standard-layer caution from M1498:

```text
standard distribution does not isolate older-history necessity;
L2 current-tiled controls remain strong;
L3 reset-control remains stronger than L3 online on this public seed.
```

## Interpretation

Supported:

```text
one-seed public plumbing works;
the matrix runner can train/evaluate all 12 profiles;
standard-layer one-seed results preserve the need for current-tiled and reset
controls in every future comparison.
```

Unsupported:

```text
controller-family ranking;
finite-window history necessity;
online recurrent advantage;
decisive-history task performance;
private-holdout generalization;
paper-level evidence;
level3 self-identification.
```

The one-seed pattern makes another immediate standard-layer repeat low leverage.
The project already has M1497 three-seed standard-profile evidence. The missing
paper-route experiment remains a controller-family-compatible decisive task
source.

## Failure Taxonomy

No runtime or process failure:

```text
failure_types: none
```

Persistent scientific blocker:

```text
scenario_sampling_failure: the standard profile layer is not decisive for
history necessity or recurrent advantage.
```

This is not an M1674 failure. It is a task-layer limitation.

## Decision

Do not run another standard-layer pilot now. Do not promote, scale to private
holdout, or interpret the one-seed pattern as ranking.

Route to:

```text
m1676-paper-route-controller-family-decisive-task-source-mapping-design
```

M1676 should design how to build or map controller-family-compatible T4/T5 task
sources. It should decide whether M1615 can only remain diagnostic, and how to
generate tasks where L1/current-tiled/reset controls cannot trivially substitute
for older command-response history.

## Guardrails

```text
private_holdout_used: false
promoted: false
profile_specific_tuning: false
actor_input_contract_changed: false
paper_level_claim_made: false
level3_self_id_claim_made: false
next: m1676-paper-route-controller-family-decisive-task-source-mapping-design
```
