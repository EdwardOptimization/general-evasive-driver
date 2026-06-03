# m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260603T192308Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: engineering_controller_route_a_hf1_p0_parity_smoke_materialization_pass
- Decision reason: M2552 materializes HF1 P0 parity-smoke artifacts status_pass true 7 actor-visible field rows cover P0 72/72 5 value-range checks 7 action mapping checks 6 external-boundary checks 33 diagnostics-exclusion checks and 8 gates pass no external simulation policy rollout training ranking validation driver-performance or self-ID claim

## Hypothesis

The Route A baseline can materialize bounded HF1 P0 parity-smoke artifacts while preserving the 72/3 no-oracle actor contract and avoiding external simulation ranking validation or driver-performance claims.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt, runs/m2532_engineering_controller_failure_surface_guarded_repair_execution/checkpoints/m2532_guarded_actor_head_repair.pt, runs/m2537_engineering_controller_failure_surface_mitigation_preserving_repair_execution/checkpoints/m2537_mitigation_preserving_actor_head_repair.pt
- parent_dataset: docs/m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design.md, docs/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.md, docs/m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit.md, runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json, runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/hf0_p0_parity_checks.csv, runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/action_mapping_checks.csv, runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/materialization_gate_matrix.csv, runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_boundary_map.csv, runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/hf0_interface_contract.md, runs/m2541_engineering_controller_route_a_baseline_and_interface_materialization/actor_io_contract_snapshot.json, docs/post-m2470-route-plan.md
- parent_config: experiments/manifests/m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design.json, experiments/manifests/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.json, experiments/manifests/m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight.json
- parent_objective: materialize the HF1 P0 parity smoke artifacts and gates designed by M2551
- derived_from: m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design, m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis, m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit, m2548-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-preflight, m2541-engineering-controller-route-a-baseline-and-interface-materialization-preflight
- blocked_by: M2551 design requires row-level HF1 P0 parity smoke artifacts before scenario taxonomy mapping or external-backend pilot planning, M2550 accepts HF0 parity/runtime readiness but rejects validation and performance interpretation, The post-M2470 Route C requires HF1 parity smoke before HF2 scenario taxonomy mapping and HF3 low-cost pilots
- supersedes: another design-only HF1 milestone without materialized parity-smoke artifacts, starting external high-fidelity simulation before HF1 parity smoke artifacts exist, claiming validation readiness from HF0 source-level parity alone, ranking Route A controllers from parity or runtime artifacts
- invalidates: None

## Success Criteria

- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_actor_visible_field_parity_rows.csv exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_observation_value_range_checks.csv exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_action_mapping_parity_checks.csv exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_external_backend_boundary_checks.csv exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/hf1_diagnostics_exclusion_checks.csv exists
- runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/materialization_gate_matrix.csv exists
- docs/m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight.md exists
- actor-visible field parity rows cover P0 indices 0 through 71 exactly with no diagnostics-only actor fields
- observation value-range checks pass with finite P0 observations
- action mapping checks pass with deployed action shape 3 and expected throttle/brake physical-control mapping
- external-backend boundary checks pass with external package imported false and external backend run false
- all diagnostics-only keys remain outside actor input
- no external high-fidelity simulation install import execution policy rollout training replay PPO ranking winner success-rate promotion validation or verdict claim is made

## Failure Criteria

- M2552 installs imports or runs Chrono or another external simulator
- M2552 changes actor input or action contract
- M2552 injects hidden or oracle actor features
- M2552 executes policy rollout or interprets parity smoke as performance
- M2552 starts training
- M2552 ranks controller families or selects a winner
- M2552 computes success rate or promotes a checkpoint
- M2552 claims high-fidelity validation paper finite-window-vs-GRU or self-ID result

## Evidence Gates

- M2552 must materialize summary actor-visible field parity observation value-range action mapping external-backend boundary diagnostics exclusion gate matrix and milestone doc artifacts
- M2552 must verify the P0 actor-visible field layout covers 72 values exactly without gaps overlaps or diagnostics-only fields
- M2552 must verify observation value-range smoke rows for ego actuator road obstacle and full-vector components
- M2552 must verify deployed action mapping parity for valid clipped invalid-shape and non-finite inputs
- M2552 must verify external-backend adapter boundary rows without installing importing or running external high-fidelity simulation
- M2552 must verify all 33 diagnostics-only keys remain outside actor input
- M2552 must preserve P0 observation shape 72 action shape 3 human_view_online_gru action_sequence_horizon 1 and no hidden/oracle actor inputs
- M2552 must not rank controller families select winners promote checkpoints compute success rates or interpret parity smoke as driver performance
- M2552 must not train replay run PPO run policy rollouts or make paper self-ID finite-window-vs-GRU current-sim high-fidelity validation or driver-performance verdict claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not install external simulator dependencies
- do not import external high-fidelity simulation packages
- do not run external high-fidelity simulation
- do not execute policy rollouts
- do not interpret parity-smoke artifacts as deployed control performance
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not change the deployed action contract
- do not inject hidden or oracle actor features
- do not add rule-switching controller modes
- do not rank controller families
- do not select a winner
- do not compute success rate or controller-family verdict metrics
- do not claim high-fidelity validation readiness
- do not claim paper-level evidence
- do not claim finite-window vs GRU conclusion
- do not claim level3 self-identification
- do not claim driver performance from parity-smoke artifacts

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit

## Scoreboard

- milestone: m2552-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-preflight
- type: infrastructure
- checkpoint: runs/m2552_engineering_controller_route_a_hf1_p0_parity_smoke_materialization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: engineering_controller_route_a_hf1_p0_parity_smoke_materialization_pass
- reason: M2552 materializes HF1 P0 parity-smoke artifacts status_pass true 7 actor-visible field rows cover P0 72/72 5 value-range checks 7 action mapping checks 6 external-boundary checks 33 diagnostics-exclusion checks and 8 gates pass no external simulation policy rollout training ranking validation driver-performance or self-ID claim

## Next Blocker

m2553-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-materialization-result-audit
