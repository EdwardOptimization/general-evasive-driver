# m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization Research Review

## Summary

- Generated at UTC: 20260602T053924Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: offtrack_guardrail_repair_spec_materialization_pass_route_to_result_audit
- Decision reason: M2371 materializes 320 repair specs priority 26 ordinary 10 guarded 18 collision 28 R4 48 diagnostic 190 exclusion counts 0 guardrail 0 no repair execution/training claims

## Hypothesis

Artifact-only materialization can turn M2368 target/guardrail rows into repair-spec artifacts without executing repair, ranking, or claiming training success.

## Lineage

- parent_checkpoint: not_applicable_artifact_only_repair_spec_materialization
- parent_dataset: docs/m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design.md, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/diagnostic_guardrail_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design.json
- parent_objective: materialize artifact-only repair specs for offtrack targets and guardrails
- derived_from: m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design, m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit
- blocked_by: M2370 designs repair specs but does not materialize them, repair implementation requires explicit target/guardrail spec artifacts
- supersedes: direct training from target rows, unbounded repair design without collision/R4/diagnostic guardrails
- invalidates: None

## Success Criteria

- runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json exists
- source offtrack, collision, R4, and diagnostic row counts match M2368
- ordinary_offtrack_repair_spec_count is greater than 0
- mixed_guarded_repair_spec_count is greater than 0
- collision_guardrail_spec_count is greater than 0
- r4_guardrail_spec_count is greater than 0
- diagnostic_guardrail_spec_count is greater than 0
- profile_or_pack_repair_spec_count r4_ordinary_repair_spec_count collision_blind_mixed_repair_spec_count are 0
- guardrail_violation_count equals 0
- environment_rollout_started policy_action_executed training_started replay_started ppo_used are false
- ranking, winner, paper-level, finite-window-vs-GRU, level3 self-ID, scenario-redesign-executed, and training-repair-success claims are false

## Failure Criteria

- summary is missing
- source counts differ from M2368
- any target family is missing
- ordinary repair specs include profile/pack/global diagnostic rows or R4 rows
- mixed repair specs omit collision guardrails
- any forbidden execution or ranking flag is set
- result audit route is missing

## Evidence Gates

- M2371 must materialize repair-spec rows from consolidated target and guardrail artifacts
- M2371 must not execute repair levers, training, reset, rollout, replay, or PPO
- M2371 must keep profile/pack diagnostic rows and R4 semantics out of ordinary repair specs

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
- do not rank support policies or controller families
- do not select a winner
- do not overwrite the active scenario config
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- objective_overfit
- behavior_regression

## Scoreboard

- milestone: m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization
- type: infrastructure
- checkpoint: runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: offtrack_guardrail_repair_spec_materialization_pass_route_to_result_audit
- reason: M2371 materializes 320 repair specs priority 26 ordinary 10 guarded 18 collision 28 R4 48 diagnostic 190 exclusion counts 0 guardrail 0 no repair execution/training claims

## Next Blocker

m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit
