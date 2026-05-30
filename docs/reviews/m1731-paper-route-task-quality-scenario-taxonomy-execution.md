# m1731-paper-route-task-quality-scenario-taxonomy-execution Research Review

## Summary

- Generated at UTC: 20260530T032503Z
- Type: gate
- Gate tier: process
- Promotion decision: scenario_taxonomy_execution_failed_route_to_sampling_failure_audit
- Decision reason: M1731 preserves metadata and guardrails but fails execution gate with 422 completed episodes and 442 scenario-sampling failures

## Hypothesis

The M1728 scenario taxonomy matrix can be executed as a fixed public diagnostic run with complete scenario aggregates and preserved unsupported-feature boundaries.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1730-paper-route-task-quality-scenario-taxonomy-execution-design.md, runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.json, runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_matrix.csv
- parent_config: experiments/manifests/m1730-paper-route-task-quality-scenario-taxonomy-execution-design.json
- parent_objective: execute measured scenario taxonomy over fixed 864-cell matrix
- derived_from: m1730-paper-route-task-quality-scenario-taxonomy-execution-design
- blocked_by: need measured execution before scenario taxonomy result audit
- supersedes: direct scenario taxonomy result audit without execution
- invalidates: None

## Success Criteria

- runs/m1731_task_quality_scenario_taxonomy_execution/summary.json exists
- episode_count == 864
- failure_count == 0
- all_selected_metrics_finite == true
- guardrail_violation_count == 0
- scenario_family_aggregate.csv exists with 6 rows
- hidden dynamics, road boundary, obstacle timing, outcome, termination, profile-outcome, and scenario-family-outcome aggregates exist
- scenario metadata fields are preserved in episode rows
- unsupported_faults_treated_as_covered == false
- training replay PPO promotion private holdout actor-input changes ranking and level3 claims remain blocked

## Failure Criteria

- episode_count != 864
- failure_count != 0
- selected metrics are non-finite
- required aggregates are missing
- scenario metadata join is missing
- unsupported faults are treated as covered
- training replay PPO private holdout promotion actor-input changes or profile ranking occurs

## Evidence Gates

- M1731 must execute exactly the M1728 864-cell scenario taxonomy matrix
- M1731 must join scenario_specs.json metadata into every episode row
- M1731 must write episode, failure, state, scenario-family, hidden-dynamics, road-boundary, obstacle-timing, outcome, termination, profile-outcome, and scenario-family-outcome artifacts
- M1731 must preserve unsupported-fault boundaries and not treat unsupported faults as covered
- M1731 must not train replay PPO promote use private holdout change actor inputs tune profiles or rank controller families

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not rank controller families
- do not treat unsupported faults as covered
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1731-paper-route-task-quality-scenario-taxonomy-execution
- type: gate
- checkpoint: runs/m1731_task_quality_scenario_taxonomy_execution/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scenario_taxonomy_execution_failed_route_to_sampling_failure_audit
- reason: M1731 preserves metadata and guardrails but fails execution gate with 422 completed episodes and 442 scenario-sampling failures

## Next Blocker

m1732-paper-route-task-quality-scenario-taxonomy-result-audit
