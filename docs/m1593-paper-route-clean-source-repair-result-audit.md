# M1593 Paper-Route Clean-Source Repair Result Audit

## Summary

M1593 audits M1592.

Decision:

```text
clean_source_repair_audit_admit_selector_balanced_cap_design_before_any_rerun
```

M1592 is a near-pass, not a pass. It substantially improves the clean
history-vs-control surface, but it fails the pre-registered max clean
source-edge share gate by a narrow margin:

```text
max_clean_source_edge_share: 0.35294117647058826
gate: <= 0.35
```

The next step may be a design-only selector-balanced cap repair. It must not
run another implementation, rerun the simulator, relax the threshold, export a
training corpus, materialize candidates, start PPO, or promote anything.

## M1592 Evidence

M1592 public result:

```text
source_spec_count: 480
selected_pair_count: 96
selected_source_edge_count: 7
selected_endpoint_source_family_count: 6
selected_window_count: 6
directed_pair_count: 192
intervention_row_count: 1536
classified_directed_pair_count: 192
required_variant_coverage_complete: true
invalid_directed_pair_count: 0
clean_directed_pair_count: 34
clean_source_edge_count: 5
clean_endpoint_source_family_count: 6
max_clean_source_edge_share: 0.35294117647058826
dominated_history_positive_directed_pair_count: 39
control_only_positive_directed_pair_count: 18
history_null_all_controls_null_directed_pair_count: 101
passes_public_smoke_gates: false
passes_evidence_quality_targets: false
null_result_classification: source_concentrated_clean_surface
guardrail_violation_count: 0
```

Relative to M1588:

```text
clean directed pairs: 7 -> 34
clean source edges: 4 -> 5
clean endpoint families: 6 -> 6
invalid directed pairs: 0 -> 0
```

This is the strongest clean-surface result in the branch so far.

## Source Concentration

Clean rows by source edge:

```text
actuator_delay_step|capability_step_up: 12
curved_boundary_obstacle|t5_boundary_axis_retarget: 9
actuator_delay_step|t5_near_boundary_warmup: 6
capability_step_down|t5_near_boundary_warmup: 5
capability_step_up|t5_near_boundary_warmup: 2
```

The largest edge contributes:

```text
12 / 34 = 0.35294117647058826
```

The miss is narrow, but it is still a miss. The audit must preserve the 0.35
threshold rather than declaring a post-hoc pass.

## Dominated And Control-Only Evidence

The result also contains substantial negatives:

```text
history_positive_control_dominated: 39
control_only_positive: 18
history_null_all_controls_null: 101
```

This matters. The selector is still doing useful work by preventing
current-frame/action-history substitution from being counted as clean history
evidence.

Dominated/control-heavy edges include:

```text
capability_step_down|t5_near_boundary_warmup
capability_step_up|t5_near_boundary_warmup
capability_step_up|t5_boundary_axis_retarget
```

Any next design must treat these as diagnostics, not as hidden self-ID success.

## Supported Claims

M1593 supports:

```text
M1592 clean-source repair is not null;
the clean selector can identify many more clean rows when pair selection is targeted;
the source surface expanded from 4 clean edges to 5 clean edges;
the remaining blocker is source concentration, not missing variants or replay invalidity;
one design-only selector-balanced cap repair is justified before deciding whether to stop or pivot.
```

## Unsupported Claims

M1593 does not support:

```text
M1592 public gate pass;
candidate materialization;
training corpus export;
PPO continuation;
checkpoint promotion;
private-holdout evidence;
high-speed history sensitivity;
paper-level self-identification;
level3 anticipatory self-identification.
```

## Failure Taxonomy

```text
scenario_sampling_failure
```

The sampled clean surface is useful but too concentrated under the
pre-registered public gate.

## Route Decision

Admit a design-only milestone:

```text
m1594-paper-route-selector-balanced-clean-source-repair-design
```

The design should define a stricter source-balanced selection rule before any
rerun. Candidate design constraints should include:

```text
preserve clean selector thresholds;
do not reduce evidence standards;
cap selected pair rows per source edge more strictly than M1592;
increase selected source-edge diversity before replay;
keep dominated/control-only diagnostics explicit;
route to implementation only after design;
route to audit immediately after any implementation;
block materialization, training, PPO, promotion, private holdout, and level3 self-ID claims.
```

Do not run the implementation in M1594.

## Guardrails

```text
history_interventions_executed: false in M1593
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
m1594-paper-route-selector-balanced-clean-source-repair-design
```
