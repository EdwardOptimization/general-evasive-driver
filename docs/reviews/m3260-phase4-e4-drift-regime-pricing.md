# m3260-phase4-e4-drift-regime-pricing Research Review

## Summary

- Generated at UTC: 20260613T170650Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: e4_drift_regime_pricing_completed
- Decision reason: all protocol gates passed; 204 rows; low_mu_power_oversteer oracle-minus-tuned +0.4000 CI95 [0.1797, 0.6203]; lift_off_recovery +0.0500 CI95 [-0.0480, 0.1480]; Track F/F2 blocked on post-E4 PI review

## Hypothesis

A preregistered Phase-4 E4 Chrono drift-regime pricing panel can compare fixed v4 reflex, selection-row tuned reflex, native structured+CEM oracle, and drift-specialized oracle on frozen beyond-saturation cells with obs72 sideslip/yaw plus rear-tire telemetry before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper Track-F admission F2-training admission or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3259-phase4-e1prime-spread-revival-repricing.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e1prime_spread_revival_repricing.json, experiments/feasibility_audit/phase4_e2prime_chrono_two_regime_hardened.json, experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full.json, experiments/feasibility_audit/phase4_e4_drift_regime_pricing_prereg.json, experiments/feasibility_audit/phase4_e4_drift_regime_pricing_quick.json
- parent_config: scripts/feasibility_audit/phase4_e4_drift_regime_pricing.py, scripts/feasibility_audit/chrono_worker_client.py, scripts/feasibility_audit/chrono_backend_worker.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Track E4: price Chrono drift / beyond-saturation regimes before Track F/F2 planning, Keep Track F/F2 blocked until E4 full pricing, F1 infrastructure, and explicit PI approval all exist
- derived_from: M3259 completed E1' and kept Track F deferred behind E4., E3 full and tire telemetry milestones made obs72 sideslip/yaw plus rear-tire truth available for drift-regime pricing., The roadmap marks E4 as the lowest-numbered dependency-satisfied OPEN unit after F was deferred.
- blocked_by: Track F/F2 remain blocked after M3260 without F1 infrastructure and explicit PI approval
- supersedes: treating Track F/F2 as admitted immediately after E1'/E2'/E3 hardening, interpreting quick E4 smoke rows as a drift pricing verdict
- invalidates: changing ActiveSafetyReflexDriver inside E4, using validation rows to choose cells, seeds, candidates, or thresholds, claiming training admission, driver performance, full high-fidelity sufficiency, paper readiness, repair success, feasibility proof, Track F/F2 admission, or self-ID from M3260

## Success Criteria

- experiments/feasibility_audit/phase4_e4_drift_regime_pricing_prereg.json exists before the full run
- experiments/feasibility_audit/phase4_e4_drift_regime_pricing_quick.json exists and passed before the full run
- experiments/feasibility_audit/phase4_e4_drift_regime_pricing.json exists after the full run
- runs/feasibility_audit/phase4_e4_drift_regime_pricing/episode_rows_full.csv includes selection and validation rows for all frozen cells
- runs/feasibility_audit/phase4_e4_drift_regime_pricing/metrics_full.csv reports protocol_gates_passed=1 and track_f_admitted=0
- docs/m3260-phase4-e4-drift-regime-pricing.md reports measured and inferred sections plus the frozen claim boundary

## Failure Criteria

- M3260 runs without preregistration or quick smoke
- M3260 omits a frozen cell, validation seed stream, arm, threshold, paired readout, or failure-mode taxonomy
- M3260 uses validation rows for selection
- M3260 tunes criteria after rows are observed
- M3260 mutates ActiveSafetyReflexDriver or the actor observation contract
- M3260 admits Track F/F2, training, driver-performance, full high-fidelity sufficiency, paper, feasibility-proof, repair-success, or self-ID claims

## Evidence Gates

- M3260 must write preregistration before the full run
- M3260 must run quick smoke before the full run
- M3260 must use disjoint selection and validation seed streams
- M3260 must report at least 20 validation units per drift cell
- M3260 must exercise fixed*, tuned reflex, native structured+CEM oracle, and drift-specialized oracle arms
- M3260 must report per-cell paired CIs for oracle-minus-fixed* and oracle-minus-tuned-reflex
- M3260 must classify reflex failures as enter, stabilize, or recover failures
- M3260 must keep Track F/F2/training admission false

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run full M3260 without preregistration and quick smoke
- do not use validation rows to choose cells, seeds, candidates, thresholds, or oracle definitions
- do not edit ActiveSafetyReflexDriver
- do not mutate obs72/action3 actor observation or action semantics
- do not invoke PPO, supervised training, guarded RL, or policy checkpoint writing
- do not claim driver performance, full high-fidelity sufficiency, paper readiness, repair success, robustness result, feasibility proof, Track F/F2 admission, or self-ID from M3260

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3260-phase4-e4-drift-regime-pricing
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: e4_drift_regime_pricing_completed
- reason: all protocol gates passed; 204 rows; low_mu_power_oversteer oracle-minus-tuned +0.4000 CI95 [0.1797, 0.6203]; lift_off_recovery +0.0500 CI95 [-0.0480, 0.1480]; Track F/F2 blocked on post-E4 PI review

## Next Blocker

None recorded.
