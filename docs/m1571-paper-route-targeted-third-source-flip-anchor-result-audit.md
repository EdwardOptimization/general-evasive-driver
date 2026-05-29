# M1571 Paper-Route Targeted Third-Source Flip-Anchor Result Audit

## Summary

M1571 audits M1570.

Decision:

```text
targeted_third_source_result_audit_admit_source_diverse_history_intervention_design
```

M1570 resolves the immediate source-generation blocker. It passes public smoke
gates and evidence-quality targets with three flip source families and four
third-source flip anchors. The new third source is:

```text
t5_high_speed_close_obstacle
```

The result admits a bounded design-only history-intervention milestone. It does
not admit direct implementation, materialization, training, PPO, promotion, or a
self-identification claim.

## M1570 Evidence

M1570 result:

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
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

Flip anchors by source family:

```text
t5_boundary_axis_retarget: 5
t5_high_speed_close_obstacle: 4
t5_near_boundary_warmup: 5
```

Targeted families:

```text
t5_high_speed_close_obstacle: 4
late_reveal_boundary: 0
```

Flip anchors by window:

```text
decision_minus_24: 6
decision_minus_16: 5
reveal: 2
reveal_plus_4: 1
```

Normal outcomes among flip anchors:

```text
normal collision: 9
normal success: 3
normal non-collision non-success: 2
```

This gives the next layer a small but source-diverse active set:

```text
14 distinct flip anchors;
3 source families;
4 temporal windows;
both collision-side and success-side local flips;
4 high-speed third-source anchors.
```

## Supported Claims

M1570 supports these claims:

```text
the recoverable active-set generation branch can now produce source-diverse distinct flip anchors;
the previous third-source blocker is resolved for t5_high_speed_close_obstacle;
the generated active set is not source-singleton and not window-singleton;
the source-generation guardrails stayed clean;
the next evidence layer may be designed over M1570 flip anchors.
```

## Unsupported Claims

M1570 does not support:

```text
history necessity;
wrong-history outcome degradation;
level3 anticipatory self-identification;
late_reveal_boundary flip-anchor success;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level self-identification claims.
```

M1570 is still public source-generation evidence. It did not execute
wrong-history, donor-history, delayed-history, reset-hidden, zero-current, or
zero-action-history interventions.

## Late-Reveal Caveat

The main caveat is that `late_reveal_boundary` remains flip-null:

```text
active recoverable anchors: 17
flip anchors: 0
```

This does not invalidate M1570 because the public gate required at least one
third-source/targeted-family flip, and high-speed provided four. It does mean
that the next design must not overstate the result as broad terminal-family
coverage.

The next design should track late-reveal separately:

```text
late_reveal_anchor_count;
late_reveal_intervention_row_count;
late_reveal_history_positive_count;
late_reveal_control_positive_count;
late_reveal_null_status.
```

If late-reveal remains null under history interventions, it should be recorded
as a family-specific negative result rather than used to weaken the M1570
source-diversity pass.

## Failure Taxonomy

```text
none
```

M1570 passed its source-generation gates. The remaining caveats are claim-scope
limitations, not implementation failure:

```text
source-generation evidence only;
high-speed-only third source;
public, not private-holdout evidence;
no history-intervention evidence yet.
```

## Route Decision

Admit one design-only milestone:

```text
m1572-paper-route-source-diverse-flip-anchor-history-intervention-design
```

M1572 should design a bounded intervention experiment over the M1570 active set.
It should use:

```text
runs/m1570_targeted_third_source_flip_anchor_smoke/flip_anchor_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/targeted_flip_anchor_rows.csv
runs/m1570_targeted_third_source_flip_anchor_smoke/recoverable_active_anchor_rows.csv
```

The design should include at least these intervention families:

```text
wrong-history donor hidden;
donor response/action plus hidden;
delayed hidden;
reset hidden once at anchor;
reset hidden every step;
zero current response;
zero action history;
zero all response/action stream.
```

M1572 must pre-register source-family and window gates, including separate
high-speed and late-reveal reporting. It must also include controls strong
enough to detect current-frame substitution.

M1572 is design-only. It must not run simulator traces, history interventions,
training, PPO, private holdout, promotion, candidate materialization, or corpus
export.

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
m1572-paper-route-source-diverse-flip-anchor-history-intervention-design
```
