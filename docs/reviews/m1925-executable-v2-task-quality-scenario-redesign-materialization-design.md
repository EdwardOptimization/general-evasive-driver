# m1925-executable-v2-task-quality-scenario-redesign-materialization-design Research Review

## Summary

- Generated at UTC: 20260531T073423Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_scenario_materialization_design_admit_implementation
- Decision reason: M1925 designs an 80-source non-holdout balanced materialization subset target with 960 expected later workload cells and keeps rollout ranking and paper claims blocked

## Hypothesis

M1924 support is sufficient to define a bounded non-holdout materialization subset with 4 supported sources per feasibility-tier and role cell.

## Lineage

- parent_checkpoint: not_applicable_task_quality_scenario_redesign_materialization_design
- parent_dataset: docs/m1924-executable-v2-task-quality-scenario-redesign-source-mining-result-audit.md, runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/summary.json, runs/m1924_executable_v2_task_quality_scenario_redesign_source_mining_result_audit/joined_source_support.csv
- parent_config: experiments/manifests/m1924-executable-v2-task-quality-scenario-redesign-source-mining-result-audit.json
- parent_objective: design a bounded public materialization subset from audited source-mining support
- derived_from: m1924-executable-v2-task-quality-scenario-redesign-source-mining-result-audit
- blocked_by: M1924 admits materialization design but no executable panel has been materialized
- supersedes: directly materializing all 399 supported sources without a balanced subset design
- invalidates: None

## Success Criteria

- docs/m1925-executable-v2-task-quality-scenario-redesign-materialization-design.md exists
- selection protocol excludes paper holdout candidates
- target source count is 80 with 4 sources per 5 tiers x 4 roles
- expected controller-profile workload count is defined
- next manifest is explicit
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- selection protocol is ambiguous
- holdout candidates are included
- target counts are ambiguous
- next route is ambiguous
- controller ranking or paper-level claims are made

## Evidence Gates

- M1925 must design a bounded public materialization subset, not use holdout candidates
- M1925 must define exact selection counts across feasibility tier and role
- M1925 must keep controller-family ranking paper claims and level3 self-ID blocked
- M1925 must not run reset rollout measured execution training replay or PPO

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
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

- milestone: m1925-executable-v2-task-quality-scenario-redesign-materialization-design
- type: gate
- checkpoint: docs/m1925-executable-v2-task-quality-scenario-redesign-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_scenario_materialization_design_admit_implementation
- reason: M1925 designs an 80-source non-holdout balanced materialization subset target with 960 expected later workload cells and keeps rollout ranking and paper claims blocked

## Next Blocker

m1925-executable-v2-task-quality-scenario-redesign-materialization-design
