# m3253-phase4-e3-chrono-measurement-ac-smoke Research Review

## Summary

- Generated at UTC: 20260612T201737Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: e3_chrono_measurement_ac_protocol_smoke_passed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E3 Chrono measurement-A/C protocol smoke can collect obs72 slip-detector traces under scripted brake/steer ramps and planar overshoot recovery traces on the default Sedan/TMeasy fixture before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3251-phase4-e2-chrono-two-regime-smoke.md, docs/m3252-phase4-e2-chrono-two-regime-full.md, docs/selfid-threshold-seeking-onset-2026-06.md, docs/selfid-reflex-recovery-budget-2026-06.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e2_chrono_two_regime_full.json, experiments/feasibility_audit/slip_onset_detectability.json, experiments/feasibility_audit/reflex_overshoot_recovery.json
- parent_config: experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_prereg.json, scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_smoke.py, scripts/feasibility_audit/slip_onset_detectability.py, scripts/feasibility_audit/reflex_overshoot_recovery.py, scripts/feasibility_audit/chrono_worker_client.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E3: Chrono re-run of measurements A and C after E0 and full E2, M3253 verifies the A/C data path before any full E3 verdict or Track F checkpoint decision
- derived_from: M3248 admitted the selected Chrono vehicle fixture envelope, M3252 completed the full E2 Chrono two-regime-law verdict and left E3 as the next Track E unit, slip_onset_detectability.py defines the obs72 SlipOnsetDetector used for measurement A, reflex_overshoot_recovery.py defines the current-sim recovery-budget framing for measurement C
- blocked_by: M3253 does not provide full E3 truth definitions or safety-gating thresholds, Track F remains blocked on full E3 disposition plus CP-3 regardless of M3253 smoke result, Chrono worker currently exposes obs72 and diagnostics but not a full tire-force truth telemetry contract for measurement A
- supersedes: treating toy-sim measurement A/C as sufficient for Track F safety gating, starting Track F after E2 without any E3 Chrono A/C protocol evidence
- invalidates: interpreting M3253 quick rows as a Chrono detection-latency verdict, interpreting M3253 quick rows as a full recoverable-set budget, opening Track F before full E3 disposition and CP-3

## Success Criteria

- experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_prereg.json exists before the quick run
- experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_quick.json exists after the quick run
- runs/feasibility_audit/phase4_e3_chrono_measurement_ac/episode_rows_quick.csv includes all expected A/C quick rows
- runs/feasibility_audit/phase4_e3_chrono_measurement_ac/metrics_quick.csv reports protocol_gates_passed=1 and quick_mode_is_verdict=0
- docs/m3253-phase4-e3-chrono-measurement-ac-smoke.md reports measured and inferred sections plus the non-verdict boundary

## Failure Criteria

- M3253 runs without preregistration
- M3253 omits a measurement A axis or measurement C driver
- M3253 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3253 admits Track F or claims a full measurement A/C verdict
- M3253 invokes training or writes a policy checkpoint

## Evidence Gates

- M3253 must write the E3 A/C preregistration before any quick rollout
- M3253 must require the M3248 E0 and M3252 full E2 artifacts before the quick run
- M3253 must write measurement A long and lateral detector trace rows
- M3253 must write measurement C baseline_coast and v4_incumbent recovery trace rows
- M3253 must report finite obs72 reset and Chrono variant-match gates
- M3253 must label quick mode as non-verdict and keep Track F blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M3253 as the full E3 Chrono measurement A/C verdict
- do not tune detector thresholds, recovery thresholds, cases, or seed streams after quick rows are observed
- do not edit ActiveSafetyReflexDriver
- do not invoke PPO, supervised training, guarded RL, or policy checkpoint writing
- do not claim detection latency, full recoverable-set budget, driver performance, high-fidelity sufficiency, or self-ID from M3253
- do not admit Track F from M3253

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3253-phase4-e3-chrono-measurement-ac-smoke
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: e3_chrono_measurement_ac_protocol_smoke_passed
- reason: all structured gates passed

## Next Blocker

None recorded.
