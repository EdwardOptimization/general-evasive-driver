# M1567 Paper-Route Flip-Anchor Repair Result Audit

## Summary

M1567 audits M1566.

Decision:

```text
flip_anchor_repair_audit_admit_targeted_third_source_design
```

M1566 is a useful near-miss, not a pass. It substantially improved the
recoverable active set and reached the success-flip threshold, but it still
missed the collision-flip threshold and the third-source-family threshold.

Failure taxonomy:

```text
scenario_sampling_failure
```

The audit admits one design-only targeted repair for a third flip source family.
It does not admit direct history interventions, training, PPO, materialization,
private holdout, promotion, or a level3 self-identification claim.

## M1566 Evidence

Positive evidence:

```text
source_spec_count: 300
anchor_candidate_count: 320
replay_ok_anchor_count: 262
recoverable_boundary_anchor_count: 111
strong_recoverable_boundary_anchor_count: 59
predecision_recoverable_anchor_count: 105
active_source_family_count: 5
active_window_count: 5
max_single_active_family_share: 0.3783783783783784
distinct_success_flip_anchor_count: 8
flip_anchor_window_count: 3
guardrail_violation_count: 0
```

Remaining failures:

```text
distinct_collision_flip_anchor_count: 7
threshold: 8

flip_anchor_source_family_count: 2
threshold: 3

passes_public_smoke_gates: false
passes_evidence_quality_targets: false
```

Compared with M1563:

```text
success flips: 5 -> 8
collision flips: 5 -> 7
flip source families: 1 -> 2
recoverable anchors: 40 selected -> 111 generated
strong anchors: 27 selected -> 59 generated
```

## Source-Family Diagnosis

Recoverable anchors by family:

```text
t5_near_boundary_warmup: 42
t5_high_speed_close_obstacle: 29
t5_boundary_axis_retarget: 20
late_reveal_boundary: 18
curved_boundary_obstacle: 2
```

Strong recoverable anchors by family:

```text
t5_near_boundary_warmup: 19
t5_boundary_axis_retarget: 17
t5_high_speed_close_obstacle: 13
late_reveal_boundary: 10
```

Flip anchors by family:

```text
collision:
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 2

success:
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 3
```

The credible third-source candidates are:

```text
t5_high_speed_close_obstacle
late_reveal_boundary
```

They already have enough recoverable and strong recoverable anchors, but the
current local holds do not flip success/collision for them. This makes a
targeted third-source design justified. It is not simply chasing one public row;
there are two source families with strong active-set mass and zero flip anchors.

## Route Decision

Admit exactly one design-only milestone:

```text
m1568-paper-route-targeted-third-source-flip-anchor-design
```

M1568 should design a targeted repair for `t5_high_speed_close_obstacle` and
`late_reveal_boundary`, with `curved_boundary_obstacle` only as a diagnostic
bonus because it has too few recoverable anchors.

The design should focus on:

```text
retargeting obstacle distance/width/lateral offset around high-speed and
late-reveal near-boundary anchors;
choosing collision-sensitive windows before the outcome is fixed;
adding only pre-registered local hold probes;
tracking distinct anchor IDs rather than local variant counts;
requiring third-source flip-family evidence before history interventions.
```

Hard stop:

```text
If the targeted implementation after M1568 still fails to produce at least
three flip source families, the branch must synthesize before any further
implementation milestone.
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
m1568-paper-route-targeted-third-source-flip-anchor-design
```
