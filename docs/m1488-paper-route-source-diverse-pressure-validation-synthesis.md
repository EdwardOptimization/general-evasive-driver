# M1488 Paper-Route Source-Diverse Pressure Validation Synthesis

## Summary

M1488 synthesizes the source-diverse pressure validation branch from M1478
through M1487 before any further replay design, corpus export, PPO, or
promotion.

Synthesis decision:

```text
continue
```

Decision:

```text
source_diverse_pressure_validation_synthesis_continue_to_calibrated_bounded_replay_design
```

M1488 does not run preflight, replay, outcome interventions, train, run PPO,
promote a checkpoint, use private holdout, export corpus, or change actor
inputs.

## Evidence Summary

M1478 designed source-diverse pressure preflight over M1476 proposal candidates,
and M1479 proved those candidates were geometry-valid:

```text
M1479 selected_candidate_rows: 108
M1479 selected_neighbor_source_rows: 96
M1479 selected_unique_source_seeds: 5
M1479 selected_unique_capability_pairs: 7
M1479 relocation_clipped_share: 0.0
```

M1480 designed bounded replay, and M1481 proved the replay path was runnable and
positive, but not source-diverse in the history-positive subset:

```text
M1481 actual_replay_rows: 252
M1481 actual_replay_unique_source_seeds: 5
M1481 actual_replay_unique_capability_pairs: 7
M1481 history_positive_rows: 12
M1481 history_positive_unique_source_seeds: 1
M1481 control_positive_rows: 15
M1481 control_positive_unique_source_seeds: 1
```

M1482 audited that result as a scenario-sampling failure rather than as
source-diverse self-ID evidence. The critical split was:

```text
original source rows: 36
original normal viable rows: 36
original history positives: 12
original control positives: 15

neighbor source rows: 216
neighbor normal viable rows: 66
neighbor normal failed rows: 150
neighbor history positives: 0
```

M1483-M1485 then implemented and ran neighbor viability calibration. M1485
produced a calibrated candidate pool:

```text
M1485 selected_candidate_rows: 112
M1485 selected_neighbor_source_rows: 88
M1485 selected_original_source_rows: 8
M1485 selected_control_diagnostic_rows: 16
M1485 selected_unique_source_seeds: 5
M1485 selected_unique_capability_pairs: 6
M1485 selected_duplicate_neighbor_viability_key_rows: 0
```

M1486 designed preflight, and M1487 proved the calibrated candidates remain
geometry-valid:

```text
M1487 geometry_pass_rows: 96
M1487 selected_candidate_rows: 96
M1487 selected_neighbor_source_rows: 88
M1487 selected_original_source_rows: 8
M1487 selected_unique_source_seeds: 5
M1487 selected_unique_capability_pairs: 6
M1487 selected_unique_reveal_buckets: 6
M1487 relocation_clipped_share: 0.0
M1487 selected_duplicate_neighbor_viability_key_rows: 0
```

The new self-ID go/no-go paper-route plan changes the interpretation: calibrated
replay may continue, but it is a bounded hypothesis test, not a default proof
route for GRU belief.

## Supported Claims

Supported:

```text
1. The source-diverse pressure path can produce geometry-valid, source-step
   anchored candidates.
2. The bounded replay tool can run source-diverse pressure candidates and
   produce outcome-sensitive local rows.
3. The first replay result was positive but source-singleton.
4. Neighbor viability calibration fixed the immediate geometry/preflight
   blocker enough to justify one calibrated bounded replay attempt.
5. No actor-input contract change, training, PPO, promotion, private holdout, or
   corpus export occurred in this branch segment.
```

## Falsified Or Blocked Claims

Blocked:

```text
source-diverse history-positive replay evidence
level3 terminal-boundary self-identification
training corpus readiness
promotion readiness
GRU recurrent-belief advantage
paper-level self-ID claim
```

Falsified for the uncalibrated source-diverse pressure replay:

```text
M1479 source-diverse preflight candidates directly transfer to source-diverse
history-positive replay rows.
```

M1481 showed that direct transfer was not enough because positives remained
source-singleton and control-sensitive.

## Failure Taxonomy Summary

Primary failure type so far:

```text
scenario_sampling_failure
```

Explanation:

```text
M1481 replay diversity existed at the actual-replay level, but history-positive
rows did not become source-diverse. Neighbor rows were often too hard: their
normal branch failed before history intervention could become meaningful.
```

Current status after M1487:

```text
preflight blocker repaired
replay proof still untested for calibrated candidates
```

No evidence of these failures occurred:

```text
contract_violation
training_instability
private_holdout_contamination
promotion_gate_failure
actor_input_contract_changed
```

## Public-Gate Overfit Risk

Risk level:

```text
medium_high
```

Reasons:

```text
1. M1478-M1487 repeatedly used public M1481/M1485 artifacts.
2. M1481 positives were source-singleton.
3. M1487 preflight is still not replay evidence.
4. Continuing beyond one calibrated replay would risk a narrow public-row loop.
```

Mitigations:

```text
1. Admit only one calibrated bounded replay design/run pair.
2. Require immediate replay result audit after that run.
3. Forbid training, PPO, promotion, corpus export, private holdout, and level3
   self-ID claims from the replay smoke.
4. If calibrated replay remains source-singleton or control-explained, pivot to
   the broader L0/L1/L2/L3 self-ID go/no-go matrix.
```

## Next Branch Decision

Continue the branch, but narrowly:

```text
next: m1489-paper-route-neighbor-viability-bounded-replay-design
```

M1489 should design a bounded replay smoke over:

```text
runs/m1487_neighbor_viability_preflight_smoke/selected_candidate_rows.csv
```

The replay design must use:

```text
--geometry-aware-selector
--candidate-step-column source_step
```

The replay result must route to audit before any training, corpus export,
promotion, or go/no-go verdict.

Hard stop after the replay audit:

```text
If source-diverse history positives do not appear, or if positives are better
explained by reset/zero-current controls, stop this source-diverse pressure loop
and pivot to the L0/L1/L2/L3 go/no-go matrix from
docs/self-id-go-no-go-paper-route-plan.md.
```

This keeps the calibrated replay as one bounded test rather than an open-ended
attempt to force a self-ID proof.
