# m3255-phase4-e3-chrono-measurement-ac-full Research Review

## Summary

- Generated at UTC: 20260613T022258Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: chrono_safety_measurement_completed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E3 full Chrono measurement A/C panel can decide the Sedan/TMeasy detector-latency table and recoverable-set budget under frozen tire-truth definitions after M3253/M3254 before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3252-phase4-e2-chrono-two-regime-full.md, docs/m3253-phase4-e3-chrono-measurement-ac-smoke.md, docs/m3254-phase4-e3-chrono-tire-telemetry-smoke.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e2_chrono_two_regime_full.json, experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_quick.json, experiments/feasibility_audit/phase4_e3_chrono_tire_telemetry_quick.json
- parent_config: experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full_prereg.json, scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_full.py, scripts/feasibility_audit/phase4_e3_chrono_measurement_ac_smoke.py, scripts/feasibility_audit/chrono_worker_client.py, scripts/feasibility_audit/chrono_backend_worker.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E3: full Chrono safety-measurement A/C verdict after E2 positive and E3 telemetry availability, M3255 freezes tire-truth onset definitions, cells, seed streams, paired recovery readouts, and CP-3 readiness criteria
- derived_from: M3248 admitted the selected Chrono Sedan/TMeasy fixture envelope, M3252 completed the full E2 Sedan/TMeasy Chrono verdict and left E3 open, M3253 passed the E3 measurement A/C protocol smoke but left truth definitions unresolved, M3254 confirmed four-wheel tire-truth telemetry availability for full E3 design
- blocked_by: Track F remains blocked until M3255 completes and PI CP-3 confirms targets and budget, M3255 covers only default Sedan/TMeasy; non-Sedan E3 and broader high-fidelity sufficiency remain uncovered
- supersedes: treating M3253 quick obs72 traces as a full E3 verdict, treating M3254 telemetry availability as a recoverable-set budget
- invalidates: starting Track F from E1/E2 plus E3 smokes alone, claiming learned-policy performance or self-ID from scripted M3255 measurement rows, using safety readouts as automatic Track-F admission without PI CP-3

## Success Criteria

- experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full_prereg.json exists before the full run
- experiments/feasibility_audit/phase4_e3_chrono_measurement_ac_full.json exists after the full run
- runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/latency_rows_full.csv includes all expected measurement A rows
- runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/recovery_rows_full.csv includes all expected measurement C rows
- runs/feasibility_audit/phase4_e3_chrono_measurement_ac_full/metrics_full.csv reports protocol_gates_passed=1, track_f_admitted=0, and cp3_evidence_ready=1
- docs/m3255-phase4-e3-chrono-measurement-ac-full.md reports measured and inferred sections plus the frozen claim boundary

## Failure Criteria

- M3255 runs without full preregistration
- M3255 omits a frozen latency or recovery row
- M3255 tunes thresholds, cases, or seed streams after rows are observed
- M3255 mutates ActiveSafetyReflexDriver or the actor observation contract
- M3255 admits Track F, training, driver-performance, full high-fidelity sufficiency, paper, feasibility-proof, repair-success, or self-ID claims

## Evidence Gates

- M3255 must write the full E3 preregistration before any full rollout
- M3255 must require M3248 E0, M3252 full E2, M3253 A/C smoke, and M3254 tire telemetry smoke artifacts before running
- M3255 must run the quick smoke before the managed full harness run
- M3255 must write every frozen measurement A latency row and measurement C recovery row
- M3255 must keep obs72/action3 finite and preserve the Sedan/TMeasy variant match
- M3255 must report detector-latency and recovery-budget readouts as measured safety evidence, not as training or promotion claims
- M3255 must keep Track F blocked and only mark CP-3 evidence ready after the full protocol gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run the full panel without preregistration
- do not tune truth thresholds, cases, seed streams, recovery criteria, or safety readouts after observing quick or full rows
- do not edit ActiveSafetyReflexDriver
- do not mutate obs72/action3 actor observation or action semantics
- do not invoke PPO, supervised training, guarded RL, or policy checkpoint writing
- do not claim driver performance, full high-fidelity sufficiency, paper readiness, repair success, robustness result, feasibility proof, Track F admission, or self-ID from M3255
- do not self-approve CP-3

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3255-phase4-e3-chrono-measurement-ac-full
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: chrono_safety_measurement_completed
- reason: all structured gates passed

## Next Blocker

None recorded.
