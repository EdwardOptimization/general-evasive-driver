# m1736-paper-route-task-quality-repaired-scenario-taxonomy-execution-design Research Review

## Summary

- Generated at UTC: 20260530T035010Z
- Type: gate
- Gate tier: process
- Promotion decision: repaired_scenario_taxonomy_execution_design_route_to_branch_synthesis
- Decision reason: M1736 designs repaired execution but routes to branch synthesis before rollout because workflow cadence fired

## Hypothesis

A measured execution protocol can be designed for the M1734 repaired scenario taxonomy while preserving repair provenance and claim boundaries.

## Lineage

- parent_checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/*/seed_167400/checkpoint.pt
- parent_dataset: docs/m1735-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight-result-audit.md, runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json, runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_matrix.csv, runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/label_distribution_by_family.csv
- parent_config: experiments/manifests/m1735-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight-result-audit.json
- parent_objective: design measured execution over repaired scenario taxonomy artifacts
- derived_from: m1735-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight-result-audit
- blocked_by: need execution design before repaired scenario taxonomy policy rollout
- supersedes: direct repaired taxonomy execution without design, controller-family ranking from reset-only preflight rows
- invalidates: None

## Success Criteria

- docs/m1736-paper-route-task-quality-repaired-scenario-taxonomy-execution-design.md exists
- execution input and output artifacts are specified
- scenario metadata and sampling repair provenance joins are required
- scenario-family repair-variant sampled-label hidden-dynamics road-boundary obstacle-timing outcome termination and profile-outcome aggregates are required
- unsupported fault boundaries are preserved
- rollout execution training replay PPO promotion private holdout actor-input changes ranking and level3 claims remain blocked
- follow-up repaired execution manifest is created

## Failure Criteria

- design executes rollout
- design omits repair provenance
- design omits sampled-label or scenario-family aggregates
- design treats unsupported faults as covered
- design changes actor inputs profiles checkpoints or reward
- environment rollout training replay PPO private holdout promotion or actor-input changes occur
- controller-family ranking or level3 claims are made

## Evidence Gates

- M1736 must design measured execution over the M1734 repaired 864-cell matrix without running it
- M1736 must require scenario metadata and sampling repair provenance in every episode row
- M1736 must require scenario-family, repair-variant, hidden-dynamics, road-boundary, obstacle-timing, outcome, termination, profile-outcome, and sampled-label aggregates
- M1736 must preserve unsupported-fault boundaries
- M1736 must not train replay PPO promote use private holdout change actor inputs tune profiles rank controller families or claim paper-level evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
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

- none

## Scoreboard

- milestone: m1736-paper-route-task-quality-repaired-scenario-taxonomy-execution-design
- type: gate
- checkpoint: docs/m1736-paper-route-task-quality-repaired-scenario-taxonomy-execution-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: repaired_scenario_taxonomy_execution_design_route_to_branch_synthesis
- reason: M1736 designs repaired execution but routes to branch synthesis before rollout because workflow cadence fired

## Next Blocker

m1737-paper-route-task-quality-scenario-taxonomy-branch-synthesis
