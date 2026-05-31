# m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design Research Review

## Summary

- Generated at UTC: 20260531T102047Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_calibrated_materialization_preflight_design_admit_focused_implementation
- Decision reason: M1957 determines M1928 preflight is not an exact schema match and admits a focused no-reset M1958 preflight adapter targeting 80 specs and 960 planned workload rows

## Hypothesis

An exact calibrated materialization preflight command can be designed for the M1956 selected source subset while preserving source metadata, accepted-cell provenance, target counts, and no-execution guardrails.

## Lineage

- parent_checkpoint: not_applicable_task_quality_calibrated_materialization_preflight_command_design
- parent_dataset: docs/m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation.md, configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json, runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/summary.json, runs/m1956_executable_v2_task_quality_calibrated_source_materialization_selector/selected_sources.csv, runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv
- parent_config: experiments/manifests/m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation.json
- parent_objective: design exact calibrated materialization preflight command path for M1956 selected sources
- derived_from: m1956-executable-v2-task-quality-calibrated-source-materialization-selector-implementation
- blocked_by: M1956 creates a source-only subset but no executable-spec materialization or preflight command exists
- supersedes: direct reset validation over M1956 selected source rows without materialization/preflight design
- invalidates: None

## Success Criteria

- docs/m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design.md exists
- preflight/materialization inputs outputs and pass gates are explicit
- target source spec workload and controller-profile counts are explicit
- source metadata and accepted-cell provenance requirements are explicit
- next implementation route is explicit
- no reset rollout measured execution ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- preflight route is ambiguous
- target counts are ambiguous
- accepted-cell provenance is dropped
- next route is ambiguous
- reset rollout measured execution ranking or paper-level claims are made

## Evidence Gates

- M1957 must choose the exact preflight/materialization route for M1956 selected sources
- M1957 must specify whether existing M1928 preflight can be adapted or a focused M1958 materializer is required
- M1957 must preserve M1956 selected-source metadata and M1952 accepted-cell provenance
- M1957 must specify target counts and guardrails for the next implementation
- M1957 must keep reset rollout measured execution ranking paper and level3 claims blocked

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

- milestone: m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design
- type: gate
- checkpoint: docs/m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_calibrated_materialization_preflight_design_admit_focused_implementation
- reason: M1957 determines M1928 preflight is not an exact schema match and admits a focused no-reset M1958 preflight adapter targeting 80 specs and 960 planned workload rows

## Next Blocker

m1957-executable-v2-task-quality-calibrated-materialization-preflight-command-design
