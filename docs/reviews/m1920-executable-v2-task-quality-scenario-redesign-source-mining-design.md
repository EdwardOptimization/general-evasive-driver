# m1920-executable-v2-task-quality-scenario-redesign-source-mining-design Research Review

## Summary

- Generated at UTC: 20260531T071008Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_scenario_source_mining_design_admit_template_implementation
- Decision reason: M1920 defines source-mining schema and 640-row first-wave candidate template gates for the task-quality scenario redesign branch

## Hypothesis

The M1919 feasibility ladder can be converted into an executable source-mining design with positive-support gates and ranking blocked.

## Lineage

- parent_checkpoint: not_applicable_task_quality_scenario_redesign_source_mining_design
- parent_dataset: docs/m1919-executable-v2-task-quality-scenario-redesign-plan.md, docs/m1918-executable-v2-support-first-task-quality-repair-axis-measured-branch-synthesis.md, runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization/summary.json
- parent_config: experiments/manifests/m1919-executable-v2-task-quality-scenario-redesign-plan.json
- parent_objective: design source mining for the new task-quality scenario redesign branch
- derived_from: m1919-executable-v2-task-quality-scenario-redesign-plan
- blocked_by: M1919 requires fresh source mining before materialization or controller comparison
- supersedes: direct materialization without source-mining gates
- invalidates: None

## Success Criteria

- docs/m1920-executable-v2-task-quality-scenario-redesign-source-mining-design.md exists
- source-mining schema is defined
- acceptance gates are defined
- fresh-source split and holdout rules are defined
- next manifest is explicit
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- design document is missing
- source-mining schema is ambiguous
- acceptance gates do not require positive support
- next route is ambiguous
- controller ranking or paper-level claims are made

## Evidence Gates

- M1920 must define the exact source-mining artifact schema and acceptance gates
- M1920 must preserve the M1919 feasibility ladder and ranking block
- M1920 must not run reset rollout measured execution training replay PPO controller ranking paper claims or level3 self-ID

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

- milestone: m1920-executable-v2-task-quality-scenario-redesign-source-mining-design
- type: gate
- checkpoint: docs/m1920-executable-v2-task-quality-scenario-redesign-source-mining-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_scenario_source_mining_design_admit_template_implementation
- reason: M1920 defines source-mining schema and 640-row first-wave candidate template gates for the task-quality scenario redesign branch

## Next Blocker

m1920-executable-v2-task-quality-scenario-redesign-source-mining-design
