# M1560 Paper-Route Recoverable Active-Set Generator Implementation

## Summary

M1560 implements and runs the no-training recoverable active-set generator
designed in M1559.

Decision:

```text
recoverable_active_set_generator_smoke_source_concentrated_route_to_audit
```

The result is a meaningful improvement over M1556: recoverable active-set counts
are strong. However, the public gate still fails because recoverable anchors are
too concentrated in one source family. This blocks history-intervention design
until M1561 audits the concentration.

## Implementation

Added:

```text
src/autodrift/recoverable_active_set_generator.py
tests/test_recoverable_active_set_generator.py
```

The generator:

```text
builds public calibration specs;
selects source-balanced temporal anchors;
replays the fixed P0 actor to each anchor;
runs bounded multi-step local action holds;
triages anchors as already_colliding, high_margin_safe, recoverable_boundary,
or strong_recoverable_boundary;
writes source, anchor, local-hold, triage, source-family, window, guardrail,
and summary artifacts.
```

Focused tests:

```text
PYTHONPATH=src python -m pytest tests/test_recoverable_active_set_generator.py -q
4 passed
```

Smoke command:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.recoverable_active_set_generator \
  --output-dir runs/m1560_recoverable_active_set_generator_smoke \
  --seed 1843 \
  --seed-count 4 \
  --max-source-specs 240 \
  --max-anchors 256
```

## Final Result

```text
source_spec_count: 200
anchor_candidate_count: 256
replay_ok_anchor_count: 200
local_hold_row_count: 9216
local_hold_failure_count: 2016
recoverable_boundary_anchor_count: 86
strong_recoverable_boundary_anchor_count: 36
predecision_recoverable_anchor_count: 80
active_source_family_count: 5
active_window_count: 5
max_single_active_family_share: 0.45348837209302323
max_single_active_window_share: 0.38372093023255816
success_flip_count: 66
collision_flip_count: 30
already_colliding_count: 44
high_margin_safe_count: 30
high_margin_active_share: 0.0
near_boundary_collision_only_share: 0.171875
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
guardrail_violation_count: 0
```

Triage:

```text
already_colliding: 44
high_margin_safe: 30
inactive_boundary: 40
recoverable_boundary: 50
replay_failed: 56
strong_recoverable_boundary: 36
```

Source-family concentration:

```text
curved_boundary_obstacle: 1 recoverable
late_reveal_boundary: 9 recoverable
t5_boundary_axis_retarget: 19 recoverable
t5_high_speed_close_obstacle: 18 recoverable
t5_near_boundary_warmup: 39 recoverable
```

The failing public criterion is:

```text
max_single_active_family_share <= 0.35
```

Observed:

```text
max_single_active_family_share: 0.45348837209302323
```

## Interpretation

M1560 is a positive infrastructure result and a partial scientific positive:

```text
multi-step local holds expose many recoverable terminal-boundary anchors;
recoverable anchors are source-family and window diverse in absolute count;
the branch is no longer blocked by absence of recoverable active-set rows.
```

But it is not materializable:

```text
recoverable anchors are too concentrated in t5_near_boundary_warmup;
the source-balance public gate fails;
history interventions remain blocked.
```

This is not a self-identification result. M1560 only proves that the generator
can produce local-control-sensitive sources. It does not test wrong history,
hidden-state necessity, or recurrent self-ID.

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
m1561-paper-route-recoverable-active-set-generator-result-audit
```

M1561 must decide whether source-balanced repair is justified or whether the
generator should pivot again before any history-intervention design.
