# m1955-executable-v2-task-quality-calibrated-source-materialization-design Research Review

## Summary

- Generated at UTC: 20260531T100438Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_source_materialization_design_admit_selector_implementation
- Decision reason: M1955 designs an 80-source calibrated materialization subset from M1952 supported rows with quotas 32 anchor 24 success 8 offtrack 16 mitigation and explicit calibrated-anchor provenance checks

## Hypothesis

A calibrated materialization subset can be designed from M1952 source rows while preserving source-kind, role, surface, and calibrated-anchor provenance diversity.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_source_materialization_design
- parent_dataset: docs/m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis.md, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/summary.json, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv
- parent_config: experiments/manifests/m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis.json
- parent_objective: design calibrated source materialization subset after offtrack-support repair synthesis
- derived_from: m1954-executable-v2-task-quality-offtrack-support-repair-branch-synthesis
- blocked_by: M1954 promotes to calibrated materialization but reset/materialized execution needs exact subset design first
- supersedes: direct reset validation over all M1952 rows without materialization design
- invalidates: None

## Success Criteria

- docs/m1955-executable-v2-task-quality-calibrated-source-materialization-design.md exists
- materialization inputs outputs and pass gates are explicit
- source-kind role surface and calibrated-anchor provenance quotas are explicit
- next implementation route is explicit
- no reset rollout ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- materialization quotas are ambiguous
- design drops calibrated-anchor provenance checks
- next route is ambiguous
- ranking or paper-level claims are made

## Evidence Gates

- M1955 must design the calibrated source materialization subset target
- M1955 must preserve source-kind role surface and calibrated-anchor provenance diversity
- M1955 must specify selector inputs outputs and pass gates
- M1955 must keep reset rollout measured execution ranking paper and level3 claims blocked

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

- none

## Scoreboard

- milestone: m1955-executable-v2-task-quality-calibrated-source-materialization-design
- type: gate
- checkpoint: docs/m1955-executable-v2-task-quality-calibrated-source-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_source_materialization_design_admit_selector_implementation
- reason: M1955 designs an 80-source calibrated materialization subset from M1952 supported rows with quotas 32 anchor 24 success 8 offtrack 16 mitigation and explicit calibrated-anchor provenance checks

## Next Blocker

m1955-executable-v2-task-quality-calibrated-source-materialization-design
