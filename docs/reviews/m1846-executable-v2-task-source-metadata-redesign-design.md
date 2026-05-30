# m1846-executable-v2-task-source-metadata-redesign-design Research Review

## Summary

- Generated at UTC: 20260530T124354Z
- Type: gate
- Gate tier: process
- Promotion decision: task_source_metadata_redesign_design_admit_implementation
- Decision reason: M1846 designs support-first task/source metadata contract with role separation and context-aware claim boundaries

## Hypothesis

A support-first executable-v2 task/source metadata contract can prevent unsupported stable AES rows by requiring reset-time conditional support before materialization and separating stable AES from drift-required roles.

## Lineage

- parent_checkpoint: not_applicable_task_source_metadata_redesign_design
- parent_dataset: docs/m1845-paper-route-executable-v2-reset-time-aes-feasibility-branch-synthesis.md, docs/m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit.md, runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json
- parent_config: experiments/manifests/m1845-paper-route-executable-v2-reset-time-aes-feasibility-branch-synthesis.json
- parent_objective: design support-first executable-v2 task/source metadata contract
- derived_from: m1845-paper-route-executable-v2-reset-time-aes-feasibility-branch-synthesis
- blocked_by: M1845 pivots away from unsupported stable AES source repair
- supersedes: materialize executable-v2 rows before proving reset-time support, force stable AES labels onto drift-required or unavoidable source regions, context-insensitive claim-boundary output
- invalidates: None

## Success Criteria

- docs/m1846-executable-v2-task-source-metadata-redesign-design.md exists
- design specifies support-first source eligibility checks before materialization
- design separates stable AES-only and drift-required role metadata
- design specifies context-aware claim-boundary output requirements
- design routes to implementation without running scan reset rollout measured rollout training replay PPO ranking or paper-level claims

## Failure Criteria

- design document is missing
- design runs scan reset or rollout
- design admits source repair payload before support proof
- design keeps stable AES and drift-required roles conflated
- design changes actor inputs reward dynamics or termination behavior

## Evidence Gates

- M1846 must design support-first task/source metadata before implementation
- M1846 must separate stable AES and drift-required task roles
- M1846 must include context-aware claim-boundary output requirements
- M1846 must keep scan reset rollout measured rollout training replay PPO promotion ranking and paper-level claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run project artifact feasibility scan
- do not generate source repair payload
- do not run environment reset
- do not run environment rollout
- do not run measured rollout
- do not execute policy actions
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change reward
- do not change dynamics
- do not change termination behavior
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m1846-executable-v2-task-source-metadata-redesign-design
- type: gate
- checkpoint: docs/m1846-executable-v2-task-source-metadata-redesign-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_source_metadata_redesign_design_admit_implementation
- reason: M1846 designs support-first task/source metadata contract with role separation and context-aware claim boundaries

## Next Blocker

m1847-executable-v2-task-source-metadata-redesign-implementation
