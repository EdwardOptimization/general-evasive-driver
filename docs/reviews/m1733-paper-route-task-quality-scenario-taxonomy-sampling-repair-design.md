# m1733-paper-route-task-quality-scenario-taxonomy-sampling-repair-design Research Review

## Summary

- Generated at UTC: 20260530T033226Z
- Type: gate
- Gate tier: process
- Promotion decision: scenario_taxonomy_sampling_repair_design_admit_reset_stress_preflight
- Decision reason: M1733 designs non-mutating taxonomy sampling repair and 864-cell reset-only feasibility preflight before policy rollout

## Hypothesis

A non-mutating repair route can be designed to make the scenario taxonomy sampling-feasible before any new 864-cell policy rollout.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1732-paper-route-task-quality-scenario-taxonomy-result-audit.md, runs/m1731_task_quality_scenario_taxonomy_execution/summary.json, runs/m1731_task_quality_scenario_taxonomy_execution/failure_rows.csv, runs/m1728_task_quality_scenario_taxonomy_preflight/scenario_specs.json
- parent_config: experiments/manifests/m1732-paper-route-task-quality-scenario-taxonomy-result-audit.json
- parent_objective: design scenario taxonomy sampling repair and reset-stress preflight route
- derived_from: m1732-paper-route-task-quality-scenario-taxonomy-result-audit
- blocked_by: M1731 failed 442 cells during obstacle scenario sampling
- supersedes: direct rerun of M1731, in-place mutation of M1728 artifacts, partial-row controller-family ranking
- invalidates: None

## Success Criteria

- docs/m1733-paper-route-task-quality-scenario-taxonomy-sampling-repair-design.md exists
- S2 S5 S6 and partial S3 repair targets are documented
- reset-only sampling feasibility preflight is required before execution
- M1728 artifacts are preserved as failed evidence
- unsupported feature boundary is preserved
- rollout training replay PPO promotion private holdout actor-input changes ranking and level3 claims remain blocked
- follow-up preflight manifest is created

## Failure Criteria

- design document is missing
- design proposes direct policy rollout without reset-stress sampling preflight
- design mutates M1728 artifacts in place
- design changes actor inputs profiles checkpoints reward PPO or replay
- design treats unsupported faults as covered
- controller-family ranking or level3 claims are made

## Evidence Gates

- M1733 must design a new sampling repair route without mutating M1728 artifacts in place
- M1733 must identify S2 S5 S6 and partial S3 sampling infeasibility as the repair target
- M1733 must require reset-only sampling feasibility preflight before any policy rollout
- M1733 must preserve unsupported-fault boundaries and P0 actor input contract
- M1733 must not train replay PPO promote use private holdout change actor inputs tune profiles rank controller families or claim paper-level evidence

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
- do not mutate M1728 artifacts in place
- do not treat unsupported faults as covered
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1733-paper-route-task-quality-scenario-taxonomy-sampling-repair-design
- type: gate
- checkpoint: docs/m1733-paper-route-task-quality-scenario-taxonomy-sampling-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scenario_taxonomy_sampling_repair_design_admit_reset_stress_preflight
- reason: M1733 designs non-mutating taxonomy sampling repair and 864-cell reset-only feasibility preflight before policy rollout

## Next Blocker

m1734-paper-route-task-quality-scenario-taxonomy-sampling-repair-preflight
