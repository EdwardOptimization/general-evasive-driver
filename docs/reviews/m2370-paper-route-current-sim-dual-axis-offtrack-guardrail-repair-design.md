# m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design Research Review

## Summary

- Generated at UTC: 20260602T052957Z
- Type: gate
- Gate tier: process
- Promotion decision: offtrack_guardrail_repair_design_admit_artifact_only_repair_spec_materializer
- Decision reason: M2370 freezes repair families ordinary offtrack mixed guarded collision guardrail R4 semantics diagnostic guardrail and admits artifact-only spec materializer no repair execution/training claims

## Hypothesis

A bounded repair design can target ordinary offtrack failures while preserving collision guardrails, R4 semantics, and diagnostic no-ranking boundaries.

## Lineage

- parent_checkpoint: not_applicable_repair_design
- parent_dataset: docs/m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit.md, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/summary.json, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/offtrack_repair_target_rows.csv, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/collision_guardrail_rows.csv, runs/m2368_paper_route_current_sim_dual_axis_actionable_target_consolidation/r4_mitigation_semantics_rows.csv, docs/self-id-go-no-go-paper-route-plan.md, docs/paper-route-finite-window-vs-gru-plan.md
- parent_config: experiments/manifests/m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit.json
- parent_objective: design a bounded offtrack repair route with collision guardrails from consolidated target artifacts
- derived_from: m2369-paper-route-current-sim-dual-axis-actionable-target-consolidation-result-audit, m2368-paper-route-current-sim-dual-axis-actionable-target-consolidation-implementation
- blocked_by: M2369 accepts target artifacts but no repair route is designed, ordinary offtrack targets require collision and R4 guardrail constraints before any repair materialization
- supersedes: direct training from consolidated target artifacts, repair design that ignores collision guardrails or R4 semantics
- invalidates: None

## Success Criteria

- docs/m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design.md exists
- ordinary offtrack repair targets and collision guardrails are specified
- R4 mitigation and diagnostic guardrails remain separate
- ranking, winner selection, paper-level, finite-window-vs-GRU, scenario-redesign-executed, training-repair, and level3 self-ID claims remain blocked
- a bounded artifact-only repair-spec materializer route is selected or branch is stopped

## Failure Criteria

- M2370 reruns reset rollout measured execution replay PPO or private holdout
- M2370 ranks support policies or controller families
- M2370 makes paper-level finite-window-vs-GRU or level3 self-ID claims
- M2370 claims scenario redesign executed or training repair success
- M2370 cannot separate offtrack targets from collision/R4/diagnostic guardrails

## Evidence Gates

- M2370 must define repair target, collision guardrail, R4, and diagnostic guardrail policies
- M2370 must choose a bounded artifact-only repair-spec materialization route or stop the branch
- M2370 must not run reset/rollout, train, rank, claim scenario redesign executed, or claim repair success

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

- milestone: m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design
- type: gate
- checkpoint: docs/m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: offtrack_guardrail_repair_design_admit_artifact_only_repair_spec_materializer
- reason: M2370 freezes repair families ordinary offtrack mixed guarded collision guardrail R4 semantics diagnostic guardrail and admits artifact-only spec materializer no repair execution/training claims

## Next Blocker

m2370-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-design
