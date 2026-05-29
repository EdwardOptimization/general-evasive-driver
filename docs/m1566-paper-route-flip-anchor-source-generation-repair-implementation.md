# M1566 Paper-Route Flip-Anchor Source-Generation Repair Implementation

## Summary

M1566 implements and runs the bounded source-generation repair designed in
M1565.

Decision:

```text
flip_anchor_source_generation_repair_smoke_near_miss_route_to_audit
```

The implementation is clean and improves the source-generation surface, but the
pre-registered public smoke gates still fail:

```text
distinct_collision_flip_anchor_count: 7
required: 8

flip_anchor_source_family_count: 2
required: 3
```

The next step is an audit, not another immediate implementation.

## Implementation

Added:

```text
src/autodrift/flip_anchor_source_generation_repair.py
tests/test_flip_anchor_source_generation_repair.py
```

Adjusted:

```text
src/autodrift/recoverable_active_set_generator.py
```

The adjustment makes `run_hold_continuation` accept an optional `override_fn`.
The default remains the original `apply_local_override`, so M1560 behavior is
unchanged unless a caller explicitly injects the M1566 repair override function.

M1566 adds bounded diagnostic local holds:

```text
full_brake_release_throttle
steer_left_full_brake
steer_right_full_brake
```

It also extends hold steps to:

```text
1, 4, 8, 12, 16
```

These are diagnostic local holds only. They are not a controller, not a
training target, and not a deployed actor output change.

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_flip_anchor_source_generation_repair.py -q
3 passed
```

Smoke command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.flip_anchor_source_generation_repair \
  --output-dir runs/m1566_flip_anchor_source_generation_repair_smoke \
  --seed 1843 \
  --seed-count 6 \
  --max-source-specs 320 \
  --max-anchors 320
```

## Result

```text
source_spec_count: 300
anchor_candidate_count: 320
replay_ok_anchor_count: 262
local_hold_row_count: 19200
local_hold_failure_count: 3480
recoverable_boundary_anchor_count: 111
strong_recoverable_boundary_anchor_count: 59
predecision_recoverable_anchor_count: 105
active_source_family_count: 5
active_window_count: 5
max_single_active_family_share: 0.3783783783783784
distinct_collision_flip_anchor_count: 7
distinct_success_flip_anchor_count: 8
distinct_any_flip_anchor_count: 10
flip_anchor_source_family_count: 2
flip_anchor_window_count: 3
max_single_flip_source_family_share: 0.5
max_single_flip_window_share: 0.5
collision_flip_variant_count: 121
success_flip_variant_count: 143
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
simulator_rerun_started: true
history_interventions_executed: false
training_corpus_exported: false
candidate_materialized: false
```

Active recoverable anchors by source family:

```text
curved_boundary_obstacle: 2
late_reveal_boundary: 18
t5_boundary_axis_retarget: 20
t5_high_speed_close_obstacle: 29
t5_near_boundary_warmup: 42
```

Flip anchors by source family:

```text
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 5
```

Flip anchors by window:

```text
decision_minus_16: 4
decision_minus_24: 5
reveal: 1
```

Triage labels:

```text
already_colliding: 47
high_margin_safe: 63
inactive_boundary: 41
recoverable_boundary: 52
replay_failed: 58
strong_recoverable_boundary: 59
```

## Interpretation

Compared with M1563, M1566 improved the active-set source distribution:

```text
recoverable anchors: 40 selected in M1563 -> 111 generated in M1566
strong recoverable anchors: 27 selected in M1563 -> 59 generated in M1566
distinct success flip anchors: 5 -> 8
distinct collision flip anchors: 5 -> 7
flip source families: 1 -> 2
```

This is a near-miss, not a pass. The repaired generator now reaches
`t5_near_boundary_warmup` flip anchors in addition to
`t5_boundary_axis_retarget`, but it still does not produce the required third
flip source family and is one collision-flip anchor short.

M1566 is not self-identification evidence. It does not run wrong-history,
reset-history, delayed-history, or donor-history interventions. It only repairs
the upstream local-control active-set source distribution.

## Guardrails

```text
history_interventions_executed: false
candidate_materialized: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```

## Next

```text
m1567-paper-route-flip-anchor-repair-result-audit
```

M1567 should decide whether this near-miss justifies a narrowly targeted third
source-family repair, or whether the recoverable active-set generation branch
should synthesize before more implementation.
