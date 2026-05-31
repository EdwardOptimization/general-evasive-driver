# m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design Research Review

## Summary

- Generated at UTC: 20260531T111335Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_offtrack_parent_tier_normalization_design_admit_implementation
- Decision reason: M1968 chooses explicit offtrack parent-tier sentinel and admits focused no-rollout implementation

## Hypothesis

Blank offtrack-boundary-relief parent_feasibility_tier_id values can be repaired by explicit metadata normalization without weakening runner validation or rerunning measured execution.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_offtrack_parent_tier_normalization_design
- parent_dataset: docs/m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit.md, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/executable_task_specs.json, runs/m1958_executable_v2_task_quality_calibrated_materialization_preflight/planned_workload.csv
- parent_config: experiments/manifests/m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit.json
- parent_objective: design explicit metadata normalization for blank offtrack-boundary-relief parent_feasibility_tier_id values
- derived_from: m1967-executable-v2-task-quality-calibrated-measured-execution-result-audit
- blocked_by: M1966 measured execution failed before rollout because offtrack-boundary-relief metadata contained blank parent_feasibility_tier_id values
- supersedes: weakening calibrated measured runner validation, rerunning measured execution before metadata normalization
- invalidates: None

## Success Criteria

- docs/m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design.md exists
- sentinel value and semantics are explicit
- runner validation remains strict
- implementation route and focused tests are specified
- repaired no-rollout materialization and reset-validation gates are specified
- no measured execution rerun ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- sentinel semantics are ambiguous
- design weakens metadata validation
- design skips repaired materialization validation
- controller ranking or paper-level claims are made

## Evidence Gates

- M1968 must design a no-rollout metadata normalization repair
- M1968 must keep runner validation strict for non-empty parent_feasibility_tier_id
- M1968 must choose explicit sentinel semantics for offtrack-boundary-relief rows
- M1968 must define validation gates for repaired materialization before measured rerun
- M1968 must not repair rerun rank or claim paper-level evidence

## Holdout Policy

- not_used

## Forbidden Shortcuts

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
- do not claim level3 self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design
- type: gate
- checkpoint: docs/m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_offtrack_parent_tier_normalization_design_admit_implementation
- reason: M1968 chooses explicit offtrack parent-tier sentinel and admits focused no-rollout implementation

## Next Blocker

m1968-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-design
