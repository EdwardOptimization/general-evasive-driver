# M1570 Paper-Route Targeted Third-Source Flip-Anchor Implementation

## Summary

M1570 implements and runs the bounded targeted third-source source-generation
repair admitted by M1569.

Decision:

```text
targeted_third_source_flip_anchor_smoke_pass_route_to_audit
```

The implementation passes the pre-registered public smoke gates and evidence
quality targets. It adds a third flip source family:

```text
t5_high_speed_close_obstacle
```

The result is a source-generation pass, not a history-necessity result. The
next milestone must audit the result before any history-intervention design.

## Implementation

Added:

```text
src/autodrift/targeted_third_source_flip_anchor.py
tests/test_targeted_third_source_flip_anchor.py
```

M1570 reuses the M1566 replay, local-hold continuation, recoverability
classification, and flip-anchor summary logic. The new runner adds:

```text
target-heavy calibration modes for t5_high_speed_close_obstacle;
target-heavy calibration modes for late_reveal_boundary;
comparison modes for existing flip families and curved diagnostics;
targeted long full-brake and brake-release local holds;
third_source_flip_anchor_count;
targeted_family_flip_anchor_count;
targeted_flip_anchor_rows.csv.
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_targeted_third_source_flip_anchor.py -q
4 passed
```

Smoke command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.targeted_third_source_flip_anchor \
  --output-dir runs/m1570_targeted_third_source_flip_anchor_smoke \
  --seed 1843 \
  --seed-count 6 \
  --max-source-specs 360 \
  --max-anchors 360
```

## Result

```text
source_spec_count: 360
anchor_candidate_count: 360
replay_ok_anchor_count: 287
local_hold_row_count: 42840
local_hold_failure_count: 8687
recoverable_boundary_anchor_count: 100
strong_recoverable_boundary_anchor_count: 59
predecision_recoverable_anchor_count: 94
active_source_family_count: 5
active_window_count: 5
max_single_active_family_share: 0.35
distinct_collision_flip_anchor_count: 11
distinct_success_flip_anchor_count: 12
distinct_any_flip_anchor_count: 14
flip_anchor_source_family_count: 3
third_source_flip_anchor_count: 4
targeted_family_flip_anchor_count: 4
flip_anchor_window_count: 4
max_single_flip_source_family_share: 0.35714285714285715
collision_flip_variant_count: 488
success_flip_variant_count: 572
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
simulator_rerun_started: true
history_interventions_executed: false
training_corpus_exported: false
candidate_materialized: false
```

Active recoverable anchors by source family:

```text
curved_boundary_obstacle: 4
late_reveal_boundary: 17
t5_boundary_axis_retarget: 21
t5_high_speed_close_obstacle: 23
t5_near_boundary_warmup: 35
```

Flip anchors by source family:

```text
t5_boundary_axis_retarget: 5
t5_high_speed_close_obstacle: 4
t5_near_boundary_warmup: 5
```

Targeted flip anchors:

```text
t5_high_speed_close_obstacle: 4
late_reveal_boundary: 0
```

Flip anchors by window:

```text
decision_minus_16: 5
decision_minus_24: 6
reveal: 2
reveal_plus_4: 1
```

Triage labels:

```text
already_colliding: 50
high_margin_safe: 95
inactive_boundary: 42
recoverable_boundary: 41
replay_failed: 73
strong_recoverable_boundary: 59
```

## Interpretation

Compared with M1566:

```text
source specs: 300 -> 360
anchor candidates: 320 -> 360
recoverable anchors: 111 -> 100
strong recoverable anchors: 59 -> 59
distinct collision flips: 7 -> 11
distinct success flips: 8 -> 12
flip source families: 2 -> 3
flip windows: 3 -> 4
third-source flip anchors: 0 -> 4
```

M1570 resolves the immediate third-source blocker. It does so through
`t5_high_speed_close_obstacle`; `late_reveal_boundary` remains active-set-rich
but flip-null under this targeted smoke.

This is enough to route to a result audit. It is not enough to route directly
to history interventions because:

```text
the evidence is still public source-generation evidence;
no wrong-history, delayed-history, reset-hidden, zero-history, or donor-history interventions were run;
the new third source is high-speed only, so late-reveal failure needs audit;
candidate materialization and corpus export remain blocked.
```

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
m1571-paper-route-targeted-third-source-flip-anchor-result-audit
```

M1571 should audit whether this source-diverse flip-anchor pass is sufficient
to admit a bounded history-intervention design, or whether the high-speed-only
third-source result still requires synthesis or another pivot.
