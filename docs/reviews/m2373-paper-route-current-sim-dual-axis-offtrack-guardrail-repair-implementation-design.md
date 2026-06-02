# m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design Research Review

## Summary

- Generated at UTC: 20260602T055549Z
- Type: gate
- Gate tier: process
- Promotion decision: bounded_repair_implementation_design_route_to_branch_synthesis
- Decision reason: M2373 designs artifact-only offtrack guardrail repair implementation route and routes to branch synthesis before materializer no repair execution/training claims

## Hypothesis

A bounded implementation design can map audited repair specs to concrete repair surfaces while preserving collision, R4, diagnostic, and claim guardrails.

## Lineage

- parent_checkpoint: not_applicable_repair_implementation_design
- parent_dataset: docs/m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit.md, docs/m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization.md, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/summary.json, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/ordinary_offtrack_repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/mixed_guarded_repair_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/collision_guardrail_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/r4_guardrail_spec_rows.csv, runs/m2371_paper_route_current_sim_dual_axis_offtrack_guardrail_repair_spec_materialization/diagnostic_guardrail_spec_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit.json
- parent_objective: design a bounded implementation route for audited offtrack guardrail repair specs without executing repair
- derived_from: m2372-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-result-audit, m2371-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-spec-materialization
- blocked_by: M2372 accepts repair specs but no implementation route is designed, repair execution remains blocked until implementation levers and guardrail preservation are specified
- supersedes: direct repair execution from repair-spec rows, training or scenario redesign that ignores collision/R4/diagnostic guardrails
- invalidates: None

## Success Criteria

- docs/m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design.md exists
- implementation levers are mapped for ordinary offtrack and mixed guarded specs
- collision, R4, and diagnostic guardrails remain constraints
- actor input, oracle-feature, profile-tuning, ranking, winner, paper-level, finite-window-vs-GRU, scenario-redesign-executed, training-repair, and level3 self-ID claims remain blocked
- a bounded follow-up route or branch synthesis route is selected

## Failure Criteria

- M2373 reruns reset rollout measured execution replay PPO or private holdout
- M2373 executes repair levers or trains
- M2373 changes actor inputs or injects hidden/oracle features
- M2373 ranks support policies or controller families
- M2373 makes paper-level finite-window-vs-GRU or level3 self-ID claims
- M2373 claims scenario redesign executed or training repair success
- M2373 ignores synthesis cadence before selecting another narrow implementation route

## Evidence Gates

- M2373 must design implementation levers for ordinary offtrack and mixed guarded repair specs without executing them
- M2373 must preserve collision, R4 mitigation, and diagnostic no-ranking guardrails as constraints
- M2373 must decide whether branch synthesis is required before any subsequent narrow implementation milestone
- M2373 must keep ranking, winner selection, paper finite-window-vs-GRU, scenario-redesign-executed, training-repair, and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not execute policy actions
- do not run measured execution
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

- milestone: m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design
- type: gate
- checkpoint: docs/m2373-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-implementation-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bounded_repair_implementation_design_route_to_branch_synthesis
- reason: M2373 designs artifact-only offtrack guardrail repair implementation route and routes to branch synthesis before materializer no repair execution/training claims

## Next Blocker

m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis
