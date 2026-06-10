# m3142-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-materialization-preflight Research Review

## Summary

- Generated at UTC: 20260608T003845Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: Pass only if M3142 materializes a bounded actor-visible residual trajectory-timing speed-envelope candidate that defaults to M3105/M3103, preserves obs72/action3 direct-action contract, writes rule contract probe requirement claim and gate artifacts, and registers M3143 audit before any measurement or repair-success interpretation.

## Hypothesis

A bounded residual trajectory-timing speed-envelope materialization can define an actor-visible obs72-to-action3 direct-action candidate that keeps M3105/M3103 as fallback and applies only capped early speed-envelope throttle suppression brake support and small steer damping under obstacle edge or stability risk before any full-fresh measurement validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof or self-ID claim.

## Lineage

- parent_checkpoint: docs/m3141-engineering-controller-active-safety-driver-m3105-residual-collision-offtrack-trajectory-timing-speed-envelope-synthesis.md, src/autodrift/engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight.py, src/autodrift/engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_materialization_preflight.py
- parent_dataset: runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/summary.json, runs/m3139_engineering_controller_active_safety_driver_m3105_incumbent_deployable_reflex_interface_materialization_preflight/residual_blocker_rows.csv, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/summary.json, runs/m3105_engineering_controller_active_safety_driver_v4_v2_fallback_no_regression_hard_safety_direct_action_repair_full_fresh_measurement_preflight/measurement_episode_rows.csv
- parent_config: experiments/manifests/m3141-engineering-controller-active-safety-driver-m3105-residual-collision-offtrack-trajectory-timing-speed-envelope-synthesis.json
- parent_objective: materialize one bounded early speed-envelope candidate for M3105 residual collision/offtrack blockers without behavior interpretation
- derived_from: m3141-engineering-controller-active-safety-driver-m3105-residual-collision-offtrack-trajectory-timing-speed-envelope-synthesis, m3140-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-result-audit, m3139-engineering-controller-active-safety-driver-m3105-incumbent-deployable-reflex-interface-materialization-preflight, m3105-engineering-controller-active-safety-driver-v4-v2-fallback-no-regression-hard-safety-direct-action-repair-full-fresh-measurement-preflight
- blocked_by: M3105 deployable incumbent still has 5 collision and 2 offtrack blockers, M3125 shows residual collision rows are late-clearance high-speed failures with terminal brake and steer authority often near exhausted, M3131 and M3137 behavior regressions make another unbounded corridor or guarded fallback branch unacceptable without a new bounded route
- supersedes: blind terminal direct-gain continuation, unmeasured standalone corridor reflex replacement
- invalidates: None

## Success Criteria

- runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight/summary.json reports status_pass true and gate_matrix_pass true
- runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight/direct_action_policy_config.json records M3105/M3103 fallback and no runtime base policy checkpoint or recurrent state
- runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight/action_probe_rows.csv includes exact fallback probes and bounded overlay probes
- runs/m3142_engineering_controller_active_safety_driver_residual_trajectory_timing_speed_envelope_materialization_preflight/residual_blocker_requirement_rows.csv preserves the seven M3139 residual blockers as requirements, not solved rows
- experiments/manifests/m3143-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-materialization-result-audit.json exists

## Failure Criteria

- M3142 requires hidden oracle TTC source route outcome verdict row-label or baseline-outcome actor inputs
- M3142 changes the obs72/action3 [steer throttle brake] runtime contract
- M3142 does not preserve M3105/M3103 as fallback default on safe and low-speed probes
- M3142 converts action probes into measurement validation repair-success or performance evidence

## Evidence Gates

- M3142 must keep M3105/M3103 as fallback default and exact safe/low-speed path
- M3142 must use only actor-visible obs72 current-frame features and direct [steer throttle brake] action output
- M3142 must cap throttle brake and steer deltas and avoid full-brake blanket behavior
- M3142 must write speed-envelope rule runtime-contract action-probe residual-requirement claim-boundary gate and summary artifacts
- M3142 must register M3143 result audit and make no measurement validation ranking promotion driver-performance current-sim verdict high-fidelity paper full-driver repair-success robustness-result feasibility-proof or self-ID claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not rerun tune expand rank promote validation or mutate checkpoints
- do not use hidden oracle target TTC source route outcome progress verdict baseline outcome row labels or M3105 blocker labels as actor inputs
- do not convert action probes or blocker requirements into measurement validation ranking promotion driver-performance current-sim robustness-result high-fidelity paper full-driver repair-success feasibility-proof or self-ID claims
- do not replace the M3105/M3103 incumbent fallback with an unmeasured standalone corridor or full-brake blanket rule

## Failure Taxonomy

- contract_violation
- lineage_invalid
- metric_artifact
- scenario_sampling_failure
- behavior_regression
- objective_overfit
- proof_washout
- seed_fragility

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

m3143-engineering-controller-active-safety-driver-residual-trajectory-timing-speed-envelope-materialization-result-audit
