# m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation Research Review

## Summary

- Generated at UTC: 20260602T182542Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_linked_repair_candidate_measured_reindex_pass_route_to_result_audit
- Decision reason: M2428 reindexes existing M2413 measured rows by M2426 matched c01/c02/c03 memberships source episodes 5250 membership rows 13050 all three candidate slices offtrack-dominated c04 excluded no rerun/ranking/verdict claims

## Hypothesis

Existing M2413 measured rows can be reindexed by the M2426 matched source-linked repair-candidate families to produce non-ranking outcome diagnostics without rerun.

## Lineage

- parent_checkpoint: not_applicable_measured_result_reindex
- parent_dataset: docs/m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit.md, runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/summary.json, runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/source_linked_family_rows.csv, runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/source_linked_scenario_rows.csv, runs/m2426_paper_route_current_sim_dual_axis_source_linked_repair_candidate_reset_evidence/reset_target_rows.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/summary.json, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_rows.csv, runs/m2413_paper_route_current_sim_dual_axis_source_linked_offtrack_containment_measured_validation/episode_family_membership_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit.json
- parent_objective: reindex existing M2413 measured rows by the M2426 matched source-linked repair-candidate family memberships
- derived_from: m2427-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-result-audit, m2426-paper-route-current-sim-dual-axis-source-linked-repair-candidate-reset-evidence-implementation, m2413-paper-route-current-sim-dual-axis-source-linked-offtrack-containment-measured-validation-implementation
- blocked_by: M2426 c04 has zero matched effective candidates and must remain excluded, M2427 rejected all-four-family measured-validation readiness, M2413 measured rows already cover the same 350 reset targets, so rerun would be duplicate local search
- supersedes: measured rerun over the same 350 reset targets, candidate family ranking from reindexed diagnostic aggregates, current-sim verdict from matched-subset reindex alone
- invalidates: None

## Success Criteria

- runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/summary.json exists
- M2426 reset keys are exactly covered by M2413 episode rows
- reindexed episode membership rows are written
- aggregate rows exist for c01 c02 and c03
- c04 is explicitly excluded with matched_effective_candidate_count 0
- rerun/reset/rollout counts remain 0
- ranking_admissible_count and winner_selected_count are 0
- guardrail_violation_count is 0

## Failure Criteria

- M2428 reruns reset or measured rollout
- M2428 executes repair or training
- M2428 ranks candidate families or selects a winner
- M2428 includes c04 as measured despite zero matched effective candidates
- M2428 hides reset-key coverage mismatch
- M2428 makes measured improvement, current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2428 must prove M2426 reset keys are exactly covered by M2413 episode rows
- M2428 must reindex existing M2413 episode rows by only the matched M2426 candidate families
- M2428 must explicitly exclude c04 outcome-failure-surface containment from measured aggregates
- M2428 must not rerun measured rollout, reset environments, execute policy actions, train, repair, replay, PPO, rank, select winners, or make verdict claims
- M2428 must preserve diagnostic-only candidate-family aggregates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun reset
- do not run measured rollout
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not overwrite active configs
- do not change actor inputs
- do not inject hidden or oracle actor features
- do not rank candidate families
- do not select a winner
- do not treat c04 as measured
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim scenario redesign executed
- do not claim training repair success
- do not claim current-sim verdict

## Failure Taxonomy

- metric_artifact
- lineage_invalid
- contract_violation
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation
- type: infrastructure
- checkpoint: runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/summary.json
- success_rate: 0.06689655172413793
- termination_rate: None
- clearance_margin_mean: 7.5792021374703
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_linked_repair_candidate_measured_reindex_pass_route_to_result_audit
- reason: M2428 reindexes existing M2413 measured rows by M2426 matched c01/c02/c03 memberships source episodes 5250 membership rows 13050 all three candidate slices offtrack-dominated c04 excluded no rerun/ranking/verdict claims

## Next Blocker

m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit
