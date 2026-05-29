# M1551 Paper-Route Calibrated Pair-Expansion Planner Result Audit

## Summary

M1551 audits M1550 before any pair-expanded intervention design.

Decision:

```text
calibrated_pair_expansion_audit_pair_gate_pass_admit_intervention_design_with_snapshot_caveat
```

M1550 is not history evidence. It did not run interventions. It is, however, a
useful source/pair result: the M1547 pair bottleneck was substantially repaired.
Accepted pairs increased from `2` to `21`, source-family edges from `1` to `5`,
terminal families to `4`, and window buckets to `3`. Pair gates passed.

The failed part is trace coverage: measured snapshot count is `13`, below the
pre-registered `24` threshold. This is a caveat, but it is not a blocker for a
bounded intervention design because the accepted pair set itself is large
enough and endpoint reuse is not concentrated.

No candidate materialization, training corpus export, history intervention,
training, PPO, promotion, private holdout, actor-input change, or level3
self-identification claim is admitted.

## Evidence

M1550 summary:

```text
terminal_base_source_rows: 20
calibration_spec_count: 200
measured_trace_count: 200
measured_snapshot_count: 13
measured_trace_family_count: 5
pair_candidate_count: 21
accepted_pair_count: 21
accepted_source_family_edge_count: 5
max_single_pair_source_edge_share: 0.38095238095238093
accepted_terminal_family_count: 4
accepted_window_bucket_count: 3
rollout_failure_count: 95
passes_trace_gates: false
passes_pair_gates: true
passes_public_smoke_gates: false
guardrail_violation_count: 0
history_interventions_executed: false
```

Accepted source-family edge counts:

```text
curved_boundary_obstacle|t5_boundary_axis_retarget: 5
curved_boundary_obstacle|t5_high_speed_close_obstacle: 5
curved_boundary_obstacle|t5_near_boundary_warmup: 8
t5_boundary_axis_retarget|t5_high_speed_close_obstacle: 1
t5_boundary_axis_retarget|t5_near_boundary_warmup: 2
```

Window bucket counts:

```text
decision|decision: 2
decision|post_decision: 10
post_decision|post_decision: 9
```

Endpoint reuse audit:

```text
max_endpoint_share: 0.14285714285714285
```

The endpoint reuse number means no single snapshot endpoint dominates the
accepted pair set. This reduces, but does not eliminate, the risk created by
the low measured snapshot count.

## Pair Gate Verdict

Verdict:

```text
pass
```

M1550 meets the pair-expansion goals that motivated the branch:

```text
accepted_pair_count >= 8
accepted_source_family_edge_count >= 5
max_single_pair_source_edge_share <= 0.4
accepted_terminal_family_count >= 4
accepted_window_bucket_count >= 2
```

This directly addresses the M1547 bottleneck. The old M1547 subset had only
two accepted pairs on one edge; the M1550 subset has 21 pairs on five edges.

## Trace Gate Verdict

Verdict:

```text
snapshot_count_fail_but_not_blocking_for_design
```

M1550 did not meet:

```text
measured_snapshot_count >= 24
```

This remains a `scenario_sampling_failure` caveat. It blocks any
materialization or paper-level claim. It does not block one bounded
intervention design because the accepted pair set already satisfies the
pair-specific gates and endpoint reuse is modest.

M1552 must preserve this caveat and report:

```text
accepted pair source-edge distribution;
endpoint reuse distribution;
anchor replay failures;
history variants versus reset/zero-current controls;
whether positives concentrate on one edge or one endpoint.
```

## Supported Claims

Supported:

```text
pairability-first planning repairs the M1547 pair bottleneck;
the pair-expanded accepted set is source-edge diverse enough for a bounded
intervention design;
the implementation preserved no-training and no-materialization guardrails.
```

## Unsupported Claims

Unsupported:

```text
history necessity;
terminal-boundary wrong-history success-drop evidence;
candidate materialization;
training corpus export;
paper-level evidence;
level3 anticipatory self-identification;
policy superiority.
```

## Failure Classification

Failure type:

```text
scenario_sampling_failure
```

Reason:

```text
measured_snapshot_count is below the pre-registered trace threshold, and
rollout failures are high enough that the next intervention result must be
audited carefully.
```

## Next Route

Admit one design milestone:

```text
m1552-paper-route-calibrated-pair-expanded-history-intervention-design
```

M1552 must not run the intervention. It must only design it.

Required design constraints:

```text
use M1550 accepted pairs;
preserve source-edge and endpoint-reuse diagnostics;
run the same core variants as M1547 if implemented later;
separate wrong-history/donor effects from reset/zero-current controls;
report concentration by source edge, endpoint, window bucket, and terminal
family;
block materialization, training, PPO, private holdout, promotion, actor-input
changes, corpus export, and level3 self-ID claims.
```

## Guardrails

```text
candidate_materialized: false
training_started: false
evaluation_started: false
replay_started: false
history_interventions_executed: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
training_corpus_exported: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
```
