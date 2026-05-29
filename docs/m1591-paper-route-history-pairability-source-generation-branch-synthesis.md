# M1591 Paper-Route History Pairability Source-Generation Branch Synthesis

## Summary

M1591 synthesizes the M1581-M1590 pairability-first source-generation branch.

Decision:

```text
history_pairability_source_generation_synthesis_continue_to_one_bounded_clean_source_implementation
```

The branch should continue, but only to exactly one bounded clean history-vs-control
source-generation implementation. The implementation must remain public,
diagnostic-only, no-training, no-materialization, and must route to an audit
whether it passes or fails.

The decision is not a promotion. It is not a paper-level self-identification
claim. It is a controlled next experiment because the branch has one real but
small clean surface and a clear selector-defined repair target.

## evidence_summary

M1581 changed the branch order:

```text
first prove matched-current hidden-divergent pairability;
then run history interventions;
then separate clean history effects from current-frame controls.
```

M1582 proved the pairability prerequisite:

```text
source_spec_count: 480
anchor_candidate_count: 640
replay_ok_anchor_count: 509
pair_screen_candidate_count: 20000
tier_a_pair_count: 20000
tier_b_pair_count: 20000
pairable_source_edge_count: 24
pairable_target_source_family_count: 8
pairable_window_count: 6
high_speed_or_late_pair_count: 108
max_single_pairable_source_edge_share: 0.0742
passes_public_smoke_gates: true
passes_evidence_quality_targets: true
guardrail_violation_count: 0
```

M1583 scoped that result: broad pairability is real, but high-speed endpoint
coverage is not solved. The written high-speed/late count came from late-reveal
coverage; the high-speed endpoint remained absent in the capped pair set.

M1584/M1585 then ran source-diverse interventions over the pairable set.
M1585 proved the intervention plumbing is live:

```text
selected_pair_count: 72
selected_source_edge_count: 19
selected_endpoint_source_family_count: 7
selected_window_count: 6
directed_pair_count: 144
intervention_row_count: 1152
anchor_replay_failure_count: 0
passes_public_smoke_gates: true
history_positive_directed_pair_count: 23
history_positive_source_edge_count: 8
max_history_margin_gap: 0.12908281005342204
```

But M1585 also falsified the broad-intervention route as evidence-quality
history necessity:

```text
passes_evidence_quality_targets: false
null_result_classification: control_dominated
control_substitution_dominated_share: 0.7184466019417476
max_current_frame_control_gap: 0.3274137328831479
history_success_drop_count: 0
```

M1587/M1588 introduced and implemented the history-vs-control selector. M1588
found a small clean surface:

```text
input_directed_pair_count: 144
classified_directed_pair_count: 144
required_variant_coverage_complete: true
clean_directed_pair_count: 7
clean_source_edge_count: 4
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.2857142857142857
dominated_history_positive_directed_pair_count: 16
control_only_positive_directed_pair_count: 28
history_null_all_controls_null_directed_pair_count: 93
passes_public_smoke_gates: true
passes_evidence_quality_targets: false
```

M1589 audited this as a selector pass with clean-count shortfall. M1590 then
designed a clean-source repair around the actual clean source edges and
dominated negatives, but correctly stopped before implementation because branch
synthesis was due.

## supported_claims

M1591 supports:

```text
matched-current hidden-divergent pairs exist at scale in the current P0 public source set;
source-diverse intervention plumbing is operational;
wrong-history and donor-plus-hidden variants can move margins on public rows;
current-frame and action-history controls can dominate many apparent history positives;
the history-vs-control selector cleanly separates clean, dominated, control-only, and null rows;
a small clean history-control separated public surface exists across 4 source edges and 6 endpoint families;
one bounded clean-source implementation is justified before closing or pivoting the branch.
```

The clean source edges worth targeting are:

```text
actuator_delay_step|t5_near_boundary_warmup
actuator_delay_step|capability_step_up
curved_boundary_obstacle|t5_boundary_axis_retarget
capability_step_down|t5_near_boundary_warmup
```

## unsupported_claims

M1591 does not support:

```text
history necessity across the scenario distribution;
level3 anticipatory self-identification;
high-speed history sensitivity;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
paper-level result claims;
actor input contract changes.
```

The clean surface is public and small. It is suitable for the next diagnostic
source-generation implementation, not for training or claims about a final RL
driver.

## falsified_claims

M1591 falsifies or rejects these branch assumptions:

```text
broad pairability alone is enough for history-necessity evidence;
source-diverse interventions automatically produce clean self-ID rows;
large history margin gaps are meaningful without current-frame control comparisons;
zero-action and zero-current controls are negligible in the current public active set;
high-speed endpoint pairability/history sensitivity is solved by the M1582 capped pair set;
the M1588 clean rows are sufficient for materialization or training without source repair.
```

## failure_taxonomy_summary

```text
objective_overfit
scenario_sampling_failure
```

`objective_overfit` applies to M1585: the broad intervention objective selected
many rows where current-frame controls dominated the history variants.

`scenario_sampling_failure` applies to M1588/M1590: the clean selector works,
but the sampled clean surface is below the evidence-quality count target.

## public_gate_overfit_risk

Risk:

```text
high
```

Reasons:

```text
the clean rows are fixed public rows;
the clean count is only 7;
the same branch has already run pairability mining, interventions, selector design, selector implementation, and repair design;
continuing without synthesis would optimize local public surfaces rather than test broader evidence;
high-speed endpoint absence remains unresolved.
```

Mitigations for the next step:

```text
allow exactly one bounded implementation;
keep it no-training and no-materialization;
require the existing clean selector thresholds without relaxation;
require source-edge and endpoint-family diversity;
track dominated/control-only rows as negatives, not as hidden successes;
route to audit immediately after the implementation;
do not use private holdout, PPO, candidate materialization, or training corpus export.
```

## next_branch_decision

Continue the current branch to exactly one bounded implementation:

```text
m1592-paper-route-clean-history-control-source-generation-repair-implementation
```

The implementation should generate and classify diagnostic rows around M1590's
clean-positive source edges. It should target:

```text
clean_directed_pair_count >= 12
clean_source_edge_count >= 5
clean_endpoint_source_family_count >= 6
max_clean_source_edge_share <= 0.35
required_variant_coverage_complete == true
invalid_directed_pair_count == 0
guardrail_violation_count == 0
```

If M1592 fails, route to audit or stop. Do not run another repair immediately.

## Guardrails

```text
history_interventions_executed: false in M1591
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
m1592-paper-route-clean-history-control-source-generation-repair-implementation
```
