# m2072-paper-route-outcome-supported-decisive-repaired-reset-validation-command-design Research Review

## Summary

- Generated at UTC: 20260531T214638Z
- Type: gate
- Gate tier: process
- Promotion decision: outcome_supported_decisive_repaired_reset_command_design_route_to_existing_validator_run
- Decision reason: M2072 freezes exact reset-only command for M2070 repaired specs target 240 obs dim 72 seed base 207300 without running reset

## Hypothesis

The M2070 repaired specs can be reset-validated using the focused reset validator with target count 240 and expected observation dimension 72.

## Lineage

- parent_checkpoint: not_applicable_outcome_supported_decisive_repaired_reset_validation_command_design
- parent_dataset: docs/m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit.md, runs/m2070_paper_route_outcome_supported_decisive_reset_materialization_repair_preflight/repaired_executable_task_specs.json
- parent_config: experiments/manifests/m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit.json
- parent_objective: design exact reset-validation command for repaired outcome-supported decisive specs
- derived_from: m2071-paper-route-outcome-supported-decisive-reset-materialization-repair-result-audit
- blocked_by: M2071 admits reset-validation command design after repaired materialization audit
- supersedes: direct reset run without command design
- invalidates: None

## Success Criteria

- docs/m2072-paper-route-outcome-supported-decisive-repaired-reset-validation-command-design.md exists
- exact reset-validation command is documented
- input repaired spec path output dir eval seed base target count expected obs dim and next blocker are explicit
- no reset rollout measured execution ranking paper-level finite-window-vs-GRU or level3 claim is made

## Failure Criteria

- design doc is missing
- reset command is incomplete
- next route is ambiguous
- reset or rollout is performed

## Evidence Gates

- M2072 must freeze the exact reset-only command for M2073
- M2072 must use the M2070 repaired executable specs
- M2072 must preserve expected observation dimension 72 and target count 240
- M2072 must not run reset rollout measured execution or ranking

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not edit code
- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not treat generated rows as paper-valid tasks

## Failure Taxonomy

- none

## Scoreboard

- milestone: m2072-paper-route-outcome-supported-decisive-repaired-reset-validation-command-design
- type: gate
- checkpoint: docs/m2072-paper-route-outcome-supported-decisive-repaired-reset-validation-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: outcome_supported_decisive_repaired_reset_command_design_route_to_existing_validator_run
- reason: M2072 freezes exact reset-only command for M2070 repaired specs target 240 obs dim 72 seed base 207300 without running reset

## Next Blocker

m2073-paper-route-outcome-supported-decisive-repaired-reset-validation-implementation-and-run
