# M1736 Paper-Route Task-Quality Repaired Scenario Taxonomy Execution Design

- status: completed
- decision: `repaired_scenario_taxonomy_execution_design_route_to_branch_synthesis`
- parent audit: `docs/m1735-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight-result-audit.md`
- repaired preflight: `runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/summary.json`

## Summary

M1736 designs measured policy execution over the M1734 repaired scenario
taxonomy. The execution should use the repaired specs and matrix that passed
reset-only feasibility, not the original M1728 specs that failed M1731.

This milestone is design-only. It does not run rollout, train, replay, run PPO,
promote, use private holdout, change actor inputs, tune profiles, rank
controller families, treat unsupported faults as covered, or claim paper-level
evidence or level3 self-identification.

## Required Inputs

M1737 should execute over:

```text
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv
runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/unsupported_scenario_features.csv
runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
runs/m1674_controller_family_one_seed_public_pilot/configs/*_seed167400.json
```

The runner must accept the M1734 JSON schema:

```text
repaired_scenario_specs.json -> repaired_scenario_specs
```

or explicitly adapt it to the M1731 execution schema before rollout. It must
not silently fall back to M1728 `scenario_specs.json`.

## Required Episode Metadata

Every M1737 episode row must preserve the M1731 scenario metadata plus M1734
repair provenance:

```text
scenario_workload_id
scenario_spec_id
m1728_scenario_spec_id
scenario_family_id
scenario_family
scenario_role
profile_name
obstacle_timing_bucket
obstacle_lateral_bucket
road_boundary_bucket
hidden_dynamics_bucket
template_source_family
allowed_labels_metadata_only
labels_enter_actor_input
sampling_repair_source
sampling_repair_variant_id
sampling_repair_applied
obstacle_label
success
collision
obstacle_completed
min_clearance_margin
termination_reason
outcome_bucket
return
steps
eval_seed
profile_config_path
checkpoint_path
```

Guardrail fields must remain false:

```text
training_started
replay_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
profile_specific_tuning
controller_family_ranking_claim_made
paper_level_claim_made
level3_self_id_claim_made
unsupported_faults_treated_as_covered
```

## Required Output Directory

M1737 should write:

```text
runs/m1737_repaired_scenario_taxonomy_execution/summary.json
runs/m1737_repaired_scenario_taxonomy_execution/episode_rows.csv
runs/m1737_repaired_scenario_taxonomy_execution/failure_rows.csv
runs/m1737_repaired_scenario_taxonomy_execution/run_state.json
runs/m1737_repaired_scenario_taxonomy_execution/profile_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/scenario_family_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/scenario_role_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/sampling_repair_variant_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/hidden_dynamics_bucket_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/road_boundary_bucket_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/obstacle_timing_bucket_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/obstacle_lateral_bucket_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/sampled_obstacle_label_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/outcome_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/termination_reason_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/profile_outcome_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/scenario_family_outcome_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/scenario_family_sampled_label_aggregate.csv
runs/m1737_repaired_scenario_taxonomy_execution/unsupported_scenario_features.csv
```

## Execution Pass/Fail Rules

M1737 passes as execution plumbing only if:

```text
episode_count == 864
failure_count == 0
all_selected_metrics_finite == true
guardrail_violation_count == 0
profile_count == 12
scenario_spec_count == 72
scenario_family_count == 6
sampling_repair_variant_aggregate_rows >= 5
sampled_obstacle_label_aggregate_rows > 0
scenario_family_sampled_label_aggregate_rows >= 9
outcome_aggregate_rows > 0
termination_reason_aggregate_rows > 0
unsupported_scenario_feature_count == 5
silent_unsupported_approximation_count == 0
unsupported_faults_treated_as_covered == false
```

Interpretation remains deferred to M1738. M1737 should not decide
controller-family ranking or scenario-family quality.

## Claim Boundary

Allowed after M1737:

```text
repaired scenario taxonomy public diagnostic execution completed;
repair provenance and sampled-label aggregates are available for audit;
unsupported fault boundaries are preserved.
```

Forbidden after M1737:

```text
controller-family ranking;
scenario taxonomy quality conclusion before M1738 audit;
private-holdout generalization;
finite-window history necessity;
paper-level evidence;
level3 self-identification.
```

## Decision

M1736 completes the repaired execution design, but the workflow synthesis cadence
has been reached. Route first to M1737 scenario taxonomy branch synthesis before
measured repaired execution. The eventual execution may update the runner or add
a thin adapter, but it must preserve the existing P0 human-view actor contract
and must not change profile configs or checkpoints.
