# m3252-phase4-e2-chrono-two-regime-full Research Review

## Summary

- Generated at UTC: 20260612T195834Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: e2_full_pricing_completed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E2 full Chrono two-regime-law pricing panel can decide whether clean-sensing belief value is positive on the default Sedan/TMeasy fixture after the M3251 protocol smoke before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3250-phase4-e1-spread-revival-pricing-full.md, docs/m3251-phase4-e2-chrono-two-regime-smoke.md, docs/selfid-threshold-seeking-regime-2026-06.md, docs/selfid-degraded-regime-final-2026-06.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e1_spread_revival_full.json, experiments/feasibility_audit/phase4_e2_chrono_two_regime_quick.json, experiments/feasibility_audit/ramp_policy_voi_regime.json, experiments/feasibility_audit/degraded_regime_final.json
- parent_config: experiments/feasibility_audit/phase4_e2_chrono_two_regime_full_prereg.json, scripts/feasibility_audit/phase4_e2_chrono_two_regime_full.py, scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py, scripts/feasibility_audit/ramp_policy_voi_regime.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E2: full Chrono version of the two-regime law after E0, E1, and M3251, M3252 decides the Sedan/TMeasy clean-sensing Chrono belief-value readout under frozen reveal tiers, mu points, seed streams, controller candidates, and paired CIs
- derived_from: M3248 admitted the selected Chrono vehicle fixture envelope, M3250 closed E1 negative and left E2/E3 open, M3251 proved the E2 threshold-seeker, oracle, fixed-ramp, and degraded-observation plumbing executes in Chrono, ramp_policy_voi_regime.py defines the current-sim clean threshold-seeker and oracle controller family
- blocked_by: Track F remains blocked on Track E plus CP-3 regardless of M3252 verdict, E3 remains a separate open Track E unit after M3252, Non-Sedan E2 generalization is not covered by M3252
- supersedes: treating M3251 quick readouts as the full E2 two-regime-law verdict, starting Track F from E1 plus E2 smoke alone
- invalidates: claiming Chrono two-regime-law scope from the toy-sim measurement without M3252, claiming self-ID, history necessity, or learned-policy performance from scripted E2 controllers, opening Track F before E3 and CP-3

## Success Criteria

- experiments/feasibility_audit/phase4_e2_chrono_two_regime_full_prereg.json exists before the full run
- experiments/feasibility_audit/phase4_e2_chrono_two_regime_full.json exists after the full run
- runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_full.csv includes all expected selection and validation rows
- runs/feasibility_audit/phase4_e2_chrono_two_regime/metrics_full.csv reports protocol_gates_passed=1
- docs/m3252-phase4-e2-chrono-two-regime-full.md reports measured and inferred sections plus the frozen verdict

## Failure Criteria

- M3252 runs without full preregistration
- M3252 uses validation rows for arm selection
- M3252 omits clean paired CIs or the delay25_tight secondary readout
- M3252 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3252 admits Track F, training, driver-performance, full high-fidelity sufficiency, paper, feasibility-proof, or self-ID claims

## Evidence Gates

- M3252 must write the full E2 preregistration before any full rollout
- M3252 must require the passed M3251 quick artifact before the full panel
- M3252 must use namespace-separated selection and validation seed streams
- M3252 must write every clean selection candidate row over frozen reveal tiers and mu points
- M3252 must choose best_seeker, best_fixed, best_floor, and oracle candidates from selection rows before validation
- M3252 must write clean validation rows and the delay25_tight secondary degraded spot
- M3252 must report paired CIs for oracle minus best_floor on every clean reveal tier
- M3252 must keep Track F blocked and make no self-ID, paper, driver-performance, promotion, or high-fidelity sufficiency claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run M3252 without the full preregistration
- do not use validation rows to choose seeker, fixed, floor, or oracle candidates
- do not tune reveal tiers, mu points, controller candidates, seed streams, degraded spots, CIs, or thresholds after observing full rows
- do not edit ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, guarded RL, or policy checkpoint writing
- do not use the delay25_tight secondary spot to open Track F
- do not claim self-ID or history necessity from M3252

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3252-phase4-e2-chrono-two-regime-full
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: e2_full_pricing_completed
- reason: all structured gates passed

## Next Blocker

None recorded.
