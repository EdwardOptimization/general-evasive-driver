# m3254-phase4-e3-chrono-tire-telemetry-smoke Research Review

## Summary

- Generated at UTC: 20260613T013953Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: tire_telemetry_smoke_passed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E3 Chrono tire-truth telemetry connector smoke can expose finite four-wheel tire slip force wheel-speed local-force and normal-load diagnostics through the Chrono worker without changing obs72 action3 actor observation or incumbent driver behavior before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3252-phase4-e2-chrono-two-regime-full.md, docs/m3253-phase4-e3-chrono-measurement-ac-smoke.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e2_chrono_two_regime_full.json, experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_quick.json
- parent_config: experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_prereg.json, scripts/feasibility_audit/phase4_e3_chrono_tire_telemetry_smoke.py, scripts/feasibility_audit/chrono_worker_client.py, scripts/feasibility_audit/chrono_backend_worker.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E3: freeze truth telemetry needed before a full Chrono measurement A/C verdict, M3254 verifies tire-truth diagnostics plumbing only; it does not decide full E3 or open Track F
- derived_from: M3248 admitted the selected Chrono vehicle fixture envelope, M3252 completed full E2 and left E3 open, M3253 passed the A/C protocol smoke but identified full E3 truth definitions as the next required dependency, Chrono vehicle tire APIs expose per-wheel slip and ReportTireForce telemetry inside the backend
- blocked_by: M3254 does not provide the full E3 detection-latency table, M3254 does not provide the full recoverable-set budget, Track F remains blocked on full E3 disposition plus CP-3 regardless of M3254 smoke result
- supersedes: treating obs72 detector traces alone as sufficient Chrono truth for full E3, starting full E3 without verifying tire-truth diagnostic availability
- invalidates: interpreting M3254 quick telemetry rows as a full E3 verdict, interpreting M3254 quick telemetry rows as Track F admission, changing actor observations or incumbent driver behavior to expose truth telemetry

## Success Criteria

- experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_prereg.json exists before the quick run
- experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_quick.json exists after the quick run
- runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/sample_rows_quick.csv includes all expected samples
- runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/wheel_rows_quick.csv includes four wheel rows per sample
- runs/feasibility_audit/phase4_e3_chrono_tire_telemetry/metrics_quick.csv reports protocol_gates_passed=1 and quick_mode_is_verdict=0
- docs/m3254-phase4-e3-chrono-tire-telemetry-smoke.md reports measured and inferred sections plus the non-verdict boundary

## Failure Criteria

- M3254 runs without preregistration
- M3254 omits a sample case or sample step
- M3254 mutates ActiveSafetyReflexDriver or the actor observation contract
- M3254 admits Track F or claims a full measurement A/C verdict
- M3254 invokes training or writes a policy checkpoint

## Evidence Gates

- M3254 must write the tire-telemetry preregistration before any quick rollout
- M3254 must require M3248 E0, M3252 full E2, and M3253 quick artifacts before the quick run
- M3254 must preserve finite obs72 samples at reset and selected steps
- M3254 must write four tire telemetry wheel rows per sample
- M3254 must report finite tire slip, wheel speed, force, local-force projection, and positive normal loads
- M3254 must label quick mode as non-verdict and keep Track F blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M3254 as the full E3 Chrono measurement A/C verdict
- do not tune detector thresholds, recovery thresholds, cases, or seed streams after quick rows are observed
- do not edit ActiveSafetyReflexDriver
- do not mutate actor observation shape or action semantics
- do not invoke PPO, supervised training, guarded RL, or policy checkpoint writing
- do not claim detection latency, full recoverable-set budget, driver performance, high-fidelity sufficiency, or self-ID from M3254
- do not admit Track F from M3254

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3254-phase4-e3-chrono-tire-telemetry-smoke
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: tire_telemetry_smoke_passed
- reason: all structured gates passed

## Next Blocker

None recorded.
