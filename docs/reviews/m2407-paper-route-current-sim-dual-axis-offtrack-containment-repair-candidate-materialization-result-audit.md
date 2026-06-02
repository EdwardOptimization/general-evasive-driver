# m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit Research Review

## Summary

- Generated at UTC: 20260602T131645Z
- Type: gate
- Gate tier: process
- Promotion decision: offtrack_containment_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter
- Decision reason: M2407 accepts M2406 compact run-dir-only overlays and guardrail metadata; routes to read-only adapter validation no repair/training/ranking/verdict claims

## Hypothesis

The M2406 run-dir-only candidate overlays can be audited into reset/load validation readiness, artifact repair, pivot, or stop decision without executing repair, training, ranking, or verdict claims.

## Lineage

- parent_checkpoint: not_applicable_offtrack_containment_repair_candidate_materialization_result_audit
- parent_dataset: docs/m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation.md, runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/summary.json, runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/repair_candidate_overlays.csv, runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/candidate_guardrail_metadata.csv, runs/m2406_paper_route_current_sim_dual_axis_offtrack_containment_repair_candidate_materialization/claim_boundary.csv, docs/m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit.md, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation.json
- parent_objective: audit M2406 run-dir-only candidate materialization and choose bounded next route
- derived_from: m2406-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-implementation, m2405-paper-route-current-sim-dual-axis-bounded-repair-plan-materialization-result-audit
- blocked_by: M2406 materializes candidate overlays but does not audit reset/load validation readiness, candidate overlays must remain non-ranking and run-dir-only, collision and R4 guardrail metadata must remain attached before any validation route
- supersedes: direct reset or rollout validation from M2406 without audit, candidate ranking from overlay families, active config overwrite from candidate overlays
- invalidates: None

## Success Criteria

- docs/m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit.md exists
- M2406 completeness and run-dir-only boundary are accepted or rejected with explicit counts
- guardrail metadata completeness is accepted or rejected
- candidates remain non-ranking
- one bounded follow-up route is selected or the branch is stopped
- blocked paper/self-ID/current-sim/training-repair claims remain blocked

## Failure Criteria

- M2407 reruns rollout or executes repair/training/replay/PPO
- M2407 ranks candidates, ranks profiles, or selects a winner
- M2407 treats candidate materialization as repair or scenario redesign success
- M2407 makes paper finite-window-vs-GRU current-sim verdict or level3 self-ID claims
- M2407 cannot classify the candidate materialization result or choose a bounded route

## Evidence Gates

- M2407 must audit M2406 candidate completeness, run-dir-only boundary, and guardrail metadata
- M2407 must decide whether to admit reset/load validation adapter design, pivot, or stop
- M2407 must keep candidates non-ranking
- M2407 must not run rollout, execute repair, train, replay, run PPO, rank candidates/profiles, overwrite active configs, or make scenario-redesign/training-repair/paper/current-sim/self-ID verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun M2397 M2399 M2401 M2404 or M2406
- do not run new rollout
- do not execute repair levers
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not inject hidden or oracle features
- do not tune controller profiles
- do not rank support policies or controller families
- do not rank effective candidates
- do not select a winner
- do not overwrite the active scenario config
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

- milestone: m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit
- type: gate
- checkpoint: docs/m2407-paper-route-current-sim-dual-axis-offtrack-containment-repair-candidate-materialization-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: offtrack_containment_repair_candidate_materialization_accepted_route_to_reset_load_validation_adapter
- reason: M2407 accepts M2406 compact run-dir-only overlays and guardrail metadata; routes to read-only adapter validation no repair/training/ranking/verdict claims

## Next Blocker

m2408-paper-route-current-sim-dual-axis-offtrack-containment-candidate-reset-load-validation-adapter-implementation
