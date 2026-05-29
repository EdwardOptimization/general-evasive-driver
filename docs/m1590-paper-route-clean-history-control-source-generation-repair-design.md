# M1590 Paper-Route Clean History-Control Source-Generation Repair Design

## Summary

M1590 designs the clean history-vs-control source-generation repair after the
M1588 selector shortfall.

Decision:

```text
clean_history_control_source_generation_repair_design_route_to_branch_synthesis_before_implementation
```

The repair target is well defined, but the current branch has reached the
workflow synthesis cadence. The next step is not another implementation
milestone. It is a branch synthesis that decides whether the clean-source repair
should be run, narrowed, pivoted, or stopped.

No simulator rollout, intervention replay, candidate materialization, training,
PPO, private holdout, actor-input change, or promotion is admitted by M1590.

## Inputs Audited

M1588 selector evidence:

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
null_result_classification: selector_public_pass_clean_shortfall
```

The selector is operational. The blocker is not label quality; it is that the
clean public surface is too small for the next evidence step.

## Clean-Positive Target

The source-generation repair should target rows labeled:

```text
history_control_separated
```

The label must preserve the M1587/M1588 thresholds:

```text
history_max_gap >= 0.02
control_max_gap < 0.75 * history_max_gap
hidden_specific_gap >= 0.01
```

Rows may also remain useful when wrong-history gap is the dominant history
channel, but current-frame controls must stay first-class negatives. Do not
relax the clean threshold just to increase count.

## Positive Source Edges

M1588 clean rows identify four source edges worth targeted generation:

```text
actuator_delay_step|t5_near_boundary_warmup
actuator_delay_step|capability_step_up
curved_boundary_obstacle|t5_boundary_axis_retarget
capability_step_down|t5_near_boundary_warmup
```

The concrete clean patterns are:

```text
actuator_delay_step target, t5_near_boundary_warmup donor, reveal_plus_4:
  history gaps 0.02779 and 0.02294
  control gaps 0.00160 and 0.00133

capability_step_up target, actuator_delay_step donor, reveal_plus_4:
  history gap 0.02976
  control gap 0.00479

t5_boundary_axis_retarget target, curved_boundary_obstacle donor, decision_minus_32:
  history gaps 0.02403 and 0.03527
  control gaps 0.00715 and 0.00648

capability_step_down target, t5_near_boundary_warmup donor, decision_minus_24:
  history gap 0.02115
  control gap 0.00671
```

These patterns should guide source generation. The repair should generate more
matched-current hidden-divergent pairs around these edges and windows, then
screen them through the same selector. It should not create a broad pairability
pool and hope clean rows emerge.

## Dominated Negative Diagnostics

M1588 also identifies edges where history gap can be large but current-frame
controls dominate:

```text
capability_step_up|t5_near_boundary_warmup
capability_step_up|curved_boundary_obstacle
capability_step_up|t5_boundary_axis_retarget
capability_step_down|drive_loss_proxy
capability_step_down|capability_step_up
```

These rows are not failures of the selector. They are useful exclusion and
contrast cases. A future implementation should report whether new candidate
specs move these families into clean history-control separation or remain
control-dominated.

## Repair Design

The bounded repair objective should be:

```text
generate source specs that increase clean history-control separated rows,
while preserving source diversity and explicitly tracking dominated/control-only
negatives.
```

Candidate generation should be staged:

```text
1. Seed from the four clean source edges and their target/donor directions.
2. Retarget windows around reveal_plus_4, decision_minus_32, and decision_minus_24.
3. Use M1588 dominated/control-only edges as negative diagnostics.
4. Screen with pairability first only as a prerequisite.
5. Apply the clean selector as the actual acceptance criterion.
6. Stop if clean rows do not increase without threshold relaxation.
```

Suggested bounded implementation gates, if a later synthesis admits the
implementation:

```text
clean_directed_pair_count >= 12
clean_source_edge_count >= 5
clean_endpoint_source_family_count >= 6
max_clean_source_edge_share <= 0.35
required_variant_coverage_complete == true
invalid_directed_pair_count == 0
guardrail_violation_count == 0
```

The implementation should remain no-training and no-materialization. It should
only generate and classify diagnostic public rows.

## Caveats

High-speed endpoint absence remains unresolved. M1590 does not claim that the
current clean surface covers high-speed history sensitivity.

The current evidence is public-row evidence. It is useful for mechanism
development but not sufficient for candidate materialization, training corpus
export, private-holdout reporting, or paper-level self-identification claims.

The active branch has now produced:

```text
M1582 broad pairability pass
M1585 source-diverse intervention plumbing pass but control-dominated result
M1588 clean selector pass but clean-count shortfall
M1590 clean repair design
```

That is enough for a synthesis checkpoint before another narrow implementation.

## Route Decision

M1590 admits the following next task:

```text
m1591-paper-route-history-pairability-source-generation-branch-synthesis
```

M1591 must synthesize the M1581-M1590 branch before deciding whether to run the
bounded clean-source repair, pivot to a new source design, or stop the branch.

M1590 does not admit:

```text
candidate materialization;
training corpus export;
PPO;
promotion;
private holdout;
actor-input changes;
history interventions;
simulator rerun;
level3 self-identification claims.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

The failure is inherited from the sampled clean surface: the selector works, but
the available clean rows are not numerous enough yet.

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
m1591-paper-route-history-pairability-source-generation-branch-synthesis
```
