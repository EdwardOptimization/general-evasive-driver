# m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit Research Review

## Summary

- Generated at UTC: 20260602T183210Z
- Type: gate
- Gate tier: process
- Promotion decision: measured_reindex_offtrack_dominated_route_to_branch_synthesis
- Decision reason: M2429 accepts M2428 reindex completeness but classifies matched c01/c02/c03 slices as offtrack-dominated with c04 excluded and routes to branch synthesis no rerun/ranking/verdict claims

## Hypothesis

Auditing M2428 will determine whether the matched-subset offtrack-dominated result should trigger branch synthesis, c04 source-coverage repair, scenario-quality reassessment, or stop.

## Lineage

- parent_checkpoint: not_applicable_measured_reindex_result_audit
- parent_dataset: docs/m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation.md, runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/summary.json, runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/aggregate_by_candidate.csv, runs/m2428_paper_route_current_sim_dual_axis_source_linked_repair_candidate_measured_reindex/reindexed_episode_membership_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation.json
- parent_objective: audit M2428 measured-result reindex before deciding whether to synthesize, repair c04 coverage, reassess scenario quality, or stop
- derived_from: m2428-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-implementation
- blocked_by: M2428 matched c01/c02/c03 slices remain offtrack-dominated, M2428 explicitly excludes c04 because M2426 has zero matched effective candidates, continuing artifact-only reindexing without a scenario-quality decision would be local search
- supersedes: direct candidate-family ranking from M2428 aggregates, current-sim verdict from matched-subset reindex alone, another reindex artifact before route synthesis or scenario-quality decision
- invalidates: None

## Success Criteria

- docs/m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit.md exists
- the audit accepts or rejects M2428 explicitly
- offtrack-dominated matched-subset evidence is classified
- c04 exclusion is preserved
- a bounded non-ranking next route is selected or the branch is stopped
- no measured rollout repair training ranking or verdict claim is made

## Failure Criteria

- M2429 reruns measured validation
- M2429 executes repair or training
- M2429 ranks candidate families or selects a winner
- M2429 hides offtrack-dominated aggregate results
- M2429 treats c04 as measured
- M2429 makes measured improvement, current-sim, paper, FW-vs-GRU, or self-ID verdict claims

## Evidence Gates

- M2429 must audit M2428 result_class and aggregate_by_candidate outcomes
- M2429 must classify offtrack-dominated matched-subset evidence
- M2429 must preserve c04 exclusion and source-coverage blocker
- M2429 must choose branch synthesis, source-coverage repair, scenario-quality reassessment, bounded next evidence, or stop
- M2429 must not rerun measured rollout, repair, train, rank candidates, select winners, or make verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun M2428
- do not rerun measured rollout
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

- milestone: m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit
- type: gate
- checkpoint: docs/m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: measured_reindex_offtrack_dominated_route_to_branch_synthesis
- reason: M2429 accepts M2428 reindex completeness but classifies matched c01/c02/c03 slices as offtrack-dominated with c04 excluded and routes to branch synthesis no rerun/ranking/verdict claims

## Next Blocker

m2429-paper-route-current-sim-dual-axis-source-linked-repair-candidate-measured-reindex-result-audit
