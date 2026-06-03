# m2521-engineering-controller-bounded-measured-behavior-panel-preflight Research Review

## Summary

- Generated at UTC: 20260603T130515Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: engineering_controller_bounded_measured_behavior_panel_preflight_pass
- Decision reason: M2521 materializes bounded source-only measured behavior panel 900 telemetry rows 9 measured behavior rows 9 measured event rows 40 metric completeness rows all metrics supported seed lineage explicit mitigation reference straight_full_brake_open_loop actor contract 72/3 source_only_diagnostic no-ranking false claim flags source-only policy and open-loop action execution no external simulation training ranking success-rate verdict validation or driver-performance claims

## Hypothesis

The accepted behavior/outcome protocol can materialize a bounded source-only measured behavior panel for the admitted actor and two open-loop references while preserving actor inputs and avoiding ranking or verdict claims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis.md, docs/m2519-engineering-controller-source-only-outcome-event-instrumentation-result-audit.md, runs/m2518_engineering_controller_source_only_outcome_event_instrumentation/summary.json, runs/m2518_engineering_controller_source_only_outcome_event_instrumentation/outcome_event_rows.csv, runs/m2518_engineering_controller_source_only_outcome_event_instrumentation/outcome_metric_gap_delta.csv, docs/m2515-engineering-controller-behavior-outcome-protocol-materialization-result-audit.md, runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/row_schema.csv, runs/m2514_engineering_controller_behavior_outcome_protocol_materialization/metric_registry.csv, docs/m2502-engineering-controller-source-only-baseline-comparison-result-audit.md, runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis.json
- parent_objective: run a bounded source-only measured behavior panel under the accepted behavior/outcome protocol
- derived_from: m2520-engineering-controller-behavior-outcome-protocol-branch-synthesis, m2519-engineering-controller-source-only-outcome-event-instrumentation-result-audit, m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight
- blocked_by: M2520 closed the behavior/outcome protocol branch and identified measured behavior data as the limiting gap, M2518/M2519 left mitigation_delta_against_reference and seed unsupported until measured behavior semantics are pre-registered, source-only diagnostics must now produce bounded measured behavior rows before further interpretation
- supersedes: another source-only protocol artifact after M2520, manual behavior interpretation without measured behavior rows
- invalidates: None

## Success Criteria

- runs/m2521_engineering_controller_bounded_measured_behavior_panel/summary.json exists
- runs/m2521_engineering_controller_bounded_measured_behavior_panel/measured_behavior_rows.csv exists
- runs/m2521_engineering_controller_bounded_measured_behavior_panel/measured_event_rows.csv exists
- runs/m2521_engineering_controller_bounded_measured_behavior_panel/metric_completeness_rows.csv exists
- docs/m2521-engineering-controller-bounded-measured-behavior-panel-preflight.md exists
- artifacts cover m1154_policy_actor coast_open_loop and straight_full_brake_open_loop
- artifacts cover stable_aes drift_required_recovery and unavoidable_mitigation
- all attempted subject-role rows are retained
- all reset and step observations have shape 72
- all actions have shape 3 finite values and stay within deployed bounds
- all actor-input leak flags are false
- seed lineage and mitigation reference semantics are explicit
- no external high-fidelity simulation install import execution training replay PPO ranking winner success-rate or verdict claim is made

## Failure Criteria

- M2521 installs imports or runs Chrono or another external simulator
- M2521 changes actor input or action contract
- M2521 injects hidden or oracle actor features
- M2521 trains replays runs PPO promotes ranks or selects a winner
- M2521 computes success rate or claims driver performance
- M2521 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2521 must implement a bounded source-only measured behavior panel under engineering_controller_behavior_outcome_v0
- M2521 must cover m1154_policy_actor coast_open_loop and straight_full_brake_open_loop over the three accepted source-only role fixtures
- M2521 must preserve P0 observation shape 72 action shape 3 and the deployed action contract
- M2521 must keep fixture labels scenario labels feasibility classes hidden diagnostics oracle labels TTC required clearance reward terms and success labels out of actor input
- M2521 must retain all attempted subject-role rows and write summary.json measured_behavior_rows.csv measured_event_rows.csv metric_completeness_rows.csv and a milestone doc
- M2521 must record deterministic source-only fixture seed lineage and a pre-registered mitigation reference subject without computing rankings winners or success-rate verdicts
- M2521 must not install import or run external high-fidelity simulation
- M2521 must not train replay run PPO rank select a winner promote a checkpoint compute success-rate verdicts or claim driver performance validation paper finite-window-vs-GRU current-sim or self-ID results

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not run measured validation
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not use success labels or reward terms as actor inputs
- do not use TTC required clearance oracle stopping distance path error heading error path curvature speed_ref beta_target or controller mode as actor inputs
- do not rank controller families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from source-only measured behavior rows

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2521-engineering-controller-bounded-measured-behavior-panel-preflight
- type: infrastructure
- checkpoint: runs/m2521_engineering_controller_bounded_measured_behavior_panel/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_bounded_measured_behavior_panel_preflight_pass
- reason: M2521 materializes bounded source-only measured behavior panel 900 telemetry rows 9 measured behavior rows 9 measured event rows 40 metric completeness rows all metrics supported seed lineage explicit mitigation reference straight_full_brake_open_loop actor contract 72/3 source_only_diagnostic no-ranking false claim flags source-only policy and open-loop action execution no external simulation training ranking success-rate verdict validation or driver-performance claims

## Next Blocker

m2522-engineering-controller-bounded-measured-behavior-panel-result-audit
