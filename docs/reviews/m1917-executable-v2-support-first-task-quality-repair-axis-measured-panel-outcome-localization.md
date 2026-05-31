# m1917-executable-v2-support-first-task-quality-repair-axis-measured-panel-outcome-localization Research Review

## Summary

- Generated at UTC: 20260531T065954Z
- Type: gate
- Gate tier: process
- Promotion decision: task_quality_repair_axis_measured_panel_outcome_localization_pass_route_to_branch_synthesis
- Decision reason: M1917 classifies all 1536 M1915 rows with joint 0 clearance-only 1257 containment-collision 261 collision-offtrack 18 near-miss 644 and routes to branch synthesis

## Hypothesis

A no-rerun full-panel localization can convert M1915's complete but coarse outcome surface into interpretable task-quality conflict classes or a synthesis decision.

## Lineage

- parent_checkpoint: not_applicable_task_quality_repair_axis_measured_panel_outcome_localization
- parent_dataset: docs/m1916-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-rerun-result-audit.md, runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/episode_rows.csv, runs/m1915_executable_v2_support_first_task_quality_repair_axis_measured_wrapper_execution_rerun/summary.json
- parent_config: experiments/manifests/m1916-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-rerun-result-audit.json
- parent_objective: localize the complete M1915 panel outcome surface without rerun
- derived_from: m1916-executable-v2-support-first-task-quality-repair-axis-measured-wrapper-rerun-result-audit
- blocked_by: M1916 found the measured geometry rows count-complete but not uniformly classified into clearance/containment conflict classes
- supersedes: controller ranking from raw success fields, opening another repair loop before localization
- invalidates: None

## Success Criteria

- runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization/summary.json exists
- all 1536 M1915 rows are accounted for
- classification coverage and missingness are reported
- variant axis role and execution-kind summaries are written
- next route is explicit
- no reset rollout measured execution training replay PPO ranking or paper-level claim is made

## Failure Criteria

- localization artifact is missing
- M1917 reruns measured execution
- rows are dropped without accounting
- next route is ambiguous
- controller ranking or paper-level claims are made from the localization

## Evidence Gates

- M1917 must not rerun reset rollout or measured execution
- M1917 must consume the complete M1915 episode rows
- M1917 must assign a consistent clearance/containment/near-miss conflict class to all 1536 rows or explicitly report why a class is unavailable
- M1917 must summarize by repair-axis variant task-quality axis role surface and execution row kind
- M1917 must decide whether task-quality evidence is interpretable or whether branch synthesis is required
- M1917 must keep controller-family ranking, paper-level claims, training, replay, PPO, and level3 self-ID blocked

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

- milestone: m1917-executable-v2-support-first-task-quality-repair-axis-measured-panel-outcome-localization
- type: gate
- checkpoint: runs/m1917_executable_v2_support_first_task_quality_repair_axis_measured_panel_outcome_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: task_quality_repair_axis_measured_panel_outcome_localization_pass_route_to_branch_synthesis
- reason: M1917 classifies all 1536 M1915 rows with joint 0 clearance-only 1257 containment-collision 261 collision-offtrack 18 near-miss 644 and routes to branch synthesis

## Next Blocker

m1917-executable-v2-support-first-task-quality-repair-axis-measured-panel-outcome-localization
