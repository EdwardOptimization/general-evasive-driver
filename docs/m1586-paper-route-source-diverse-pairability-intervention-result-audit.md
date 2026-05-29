# M1586 Paper-Route Source-Diverse Pairability Intervention Result Audit

## Summary

M1586 audits M1585.

Decision:

```text
source_diverse_pairability_intervention_audit_admit_history_vs_control_active_set_selector_design
```

M1585 is a useful public-pass / evidence-quality-fail result. It proves that the
source-diverse pairability intervention harness is live, but it does not prove
history necessity. The blocker is not replay plumbing or pairability; it is
control dominance.

## M1585 Evidence

Public gates passed:

```text
selected_pair_count: 72
selected_source_edge_count: 19
selected_endpoint_source_family_count: 7
selected_window_count: 6
same_window_selected_pair_count: 72
directed_pair_count: 144
intervention_row_count: 1152
anchor_replay_failure_count: 0
passes_public_smoke_gates: true
```

History variants were not null:

```text
history_positive_directed_pair_count: 23
history_positive_source_edge_count: 8
history_positive_endpoint_source_family_count: 7
max_history_margin_gap: 0.12908281005342204
```

But evidence-quality failed:

```text
passes_evidence_quality_targets: false
null_result_classification: control_dominated
max_current_frame_control_gap: 0.3274137328831479
control_substitution_dominated_share: 0.7184466019417476
history_success_drop_count: 0
```

## Clean Versus Dominated Split

Using the M1585 criterion:

```text
history positive if history gap >= 0.02 or history success drop;
clean if control gap < 0.75 * history gap or history has unique success drop.
```

The split is:

```text
clean history-vs-control directed pairs: 7
clean source edges: 4
dominated history-positive directed pairs: 16
history-null directed pairs: 121
```

Clean source edges:

```text
actuator_delay_step|t5_near_boundary_warmup: 2
actuator_delay_step|capability_step_up: 2
curved_boundary_obstacle|t5_boundary_axis_retarget: 2
capability_step_down|t5_near_boundary_warmup: 1
```

Dominated source edges include:

```text
capability_step_up|t5_near_boundary_warmup
capability_step_up|curved_boundary_obstacle
capability_step_up|t5_boundary_axis_retarget
actuator_delay_step|capability_step_up
capability_step_down|drive_loss_proxy
capability_step_down|t5_near_boundary_warmup
```

This shows a small but real clean sub-surface. It is not yet source-diverse
enough for evidence-quality targets.

## Variant Interpretation

Variant maxima:

```text
wrong_history_hidden max gap: 0.10436934117322849
donor_response_action_plus_hidden max gap: 0.12908281005342204
donor_response_action_only max gap: 0.011708876431510973
reset_hidden max gap: 0.01229398408470983
zero_action_history max gap: 0.3274137328831479
zero_current_response max gap: 0.07821424364900809
zero_all_response max gap: 0.07821424364900809
```

The strongest control is `zero_action_history`, which suggests the current
selected anchors are highly action-history/current-response fragile. That is not
the same as recurrent hidden-state self-identification.

## High-Speed Caveat

M1585 selected set still has:

```text
high_speed_endpoint_directed_pair_count: 0
late_reveal_endpoint_directed_pair_count: 0
```

This follows from the capped M1582 pair set and M1583 audit. It remains a
diagnostic caveat, not a solved capability.

## Supported Claims

M1586 supports:

```text
source-diverse pairability intervention plumbing is live;
wrong-history and donor-plus-hidden interventions can affect margins;
some clean history-vs-control rows exist;
the broad selected set is too control-dominated for history-necessity claims.
```

## Unsupported Claims

M1586 does not support:

```text
history necessity;
source-diverse self-identification;
high-speed history sensitivity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
objective_overfit
```

The branch can create matched pairs and run interventions, but the selection
objective still admits many rows where zero-action/current-frame controls are
stronger than history surgery.

## Route Decision

Do not route to:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
another broad pairability intervention implementation.
```

Admit one design-only milestone:

```text
m1587-paper-route-history-vs-control-active-set-selector-design
```

The next design should explicitly target:

```text
history gap >= 0.02;
control gap < 0.75 * history gap;
donor_response_action_plus_hidden gap - donor_response_action_only gap >= 0.01 when available;
source-edge and endpoint-family diversity;
high-speed/late endpoint caveat tracked separately.
```

The goal is not to relax the gate. The goal is to turn M1585's clean sub-surface
into the first-class source-selection objective.

## Guardrails

```text
history_interventions_executed: false in M1586
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
m1587-paper-route-history-vs-control-active-set-selector-design
```
