# m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260607T172802Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_route_to_m3079_result_audit
- Decision reason: Completed: M3078 materialized actor-visible deterministic direct-action safety-reflex artifacts with status_pass True gate_matrix_pass True feature rows 6 rule rows 6 exclusion rows 10 measurement admission rows 12 claim rows 19 gate rows 16 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no reset step rollout replay fitting training validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3079 result audit.

## Hypothesis

A bounded materialization preflight can convert the M3077 route decision into one actor-visible deterministic obs72-to-action3 safety-reflex candidate contract, rule table, guard set, and measurement-admission package before any rollout, validation, ranking, promotion, driver-performance, paper, high-fidelity, repair-success, or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-pivot-route-design.md, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/summary.json, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/summary.json
- parent_dataset: runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/measurement_episode_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/measurement_episode_rows.csv, runs/m3067_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_closed_loop_measurement_preflight/metric_summary_rows.csv, runs/m3075_engineering_controller_active_safety_driver_v1_offtrack_dominant_behavior_direct_action_multi_failure_repair_closed_loop_measurement_preflight/metric_summary_rows.csv
- parent_config: experiments/manifests/m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-pivot-route-design.json, experiments/manifests/m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit.json
- parent_objective: materialize one deployable actor-visible deterministic direct-action safety-reflex candidate contract after M3077 route selection
- derived_from: m3077-engineering-controller-active-safety-driver-v1-deployable-direct-action-safety-reflex-pivot-route-design
- blocked_by: M3077 selected a deterministic direct-action safety-reflex materialization route but no materialized candidate contract exists yet, same-denominator measurement must not run before actor contract and claim-boundary artifacts exist
- supersedes: offline multi-failure target-fitting repair continuation as the default next route, residual/base-policy assisted route as the active-safety mainline
- invalidates: None

## Success Criteria

- summary.json reports status_pass true and gate_matrix_pass true
- actor-visible feature contract covers obs72 slices without hidden/oracle/TTC/target/provenance labels
- safety-reflex rule rows define one deterministic direct-action [steer throttle brake] policy skeleton
- direct-action policy config preserves observation shape 72 action shape 3 final action clipping and runtime_base_policy_required false
- measurement admission gates require same-denominator safety metrics before any performance claim
- M3079 result-audit manifest is created and pending

## Failure Criteria

- M3078 requires actor inputs outside obs72
- M3078 produces a residual/base-policy route instead of a full direct-action actor
- M3078 uses hidden oracle TTC target provenance source route outcome progress or verdict labels as actor input
- M3078 runs rollout fitting training validation ranking promotion or high-fidelity simulation
- M3078 makes driver-performance repair-success paper finite-window-vs-GRU full-driver or self-ID claims

## Evidence Gates

- M3078 must preserve obs72/action3 direct [steer throttle brake] actor contract
- M3078 must use actor-visible ego actuator road and obstacle features only
- M3078 must keep runtime_base_policy_required false
- M3078 must define one deterministic direct-action safety-reflex skeleton and not a fitted target tensor
- M3078 must write measurement-admission gates for collision offtrack clearance stability recovery action pressure and robustness before any measured claim
- M3078 must not run rollout fitting validation ranking promotion high-fidelity comparison or paper/self-ID evaluation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden oracle TTC target provenance source route outcome progress or verdict labels to actor input
- do not use a runtime base policy or residual-only adapter as the selected route
- do not tune denominator rows after seeing M3067/M3075 behavior counts
- do not claim validation ranking promotion driver performance current-sim verdict repair success high-fidelity readiness paper finite-window-vs-GRU full-driver or self-ID evidence

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- objective_overfit
- proof_washout

## Scoreboard

- milestone: m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight
- type: infrastructure
- checkpoint: runs/m3078_engineering_controller_active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_safety_driver_v1_actor_visible_deterministic_direct_action_safety_reflex_materialization_route_to_m3079_result_audit
- reason: Completed: M3078 materialized actor-visible deterministic direct-action safety-reflex artifacts with status_pass True gate_matrix_pass True feature rows 6 rule rows 6 exclusion rows 10 measurement admission rows 12 claim rows 19 gate rows 16 actor 72/action 3 direct_action_clipped [steer throttle brake] runtime_base_policy_required false; no reset step rollout replay fitting training validation ranking promotion driver-performance current-sim high-fidelity paper finite-window-vs-GRU full-driver repair-success or self-ID claims; registered M3079 result audit.

## Next Blocker

m3079-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-result-audit
