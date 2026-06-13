# m3251-phase4-e2-chrono-two-regime-smoke Research Review

## Summary

- Generated at UTC: 20260612T192200Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: not_applicable
- Decision reason: Accept M3251 as completed if the quick E2 panel runs under the frozen preregistration, writes JSON/CSV/doc artifacts, passes protocol gates, and keeps quick mode non-verdict with Track F blocked.

## Hypothesis

A preregistered Phase-4 E2 Chrono two-regime-law protocol smoke can port the threshold-seeker and shortfall detector controller family onto the Chrono worker interface and exercise clean plus degraded-spot rows before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3250-phase4-e1-spread-revival-pricing-full.md, docs/selfid-threshold-seeking-regime-2026-06.md, docs/selfid-degraded-regime-final-2026-06.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e1_spread_revival_full.json, experiments/feasibility_audit/ramp_policy_voi_regime.json, experiments/feasibility_audit/degraded_regime_final.json
- parent_config: experiments/feasibility_audit/phase4_e2_chrono_two_regime_prereg.json, scripts/feasibility_audit/phase4_e2_chrono_two_regime_smoke.py, scripts/feasibility_audit/ramp_policy_voi_regime.py, scripts/feasibility_audit/degraded_regime_final.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E2: Chrono version of the two-regime law after E0 and E1, M3251 verifies the controller/detector/degradation plumbing before a separate full E2 verdict milestone
- derived_from: M3248 admitted the selected Chrono vehicle fixture envelope, M3250 closed E1 negative and kept Track F blocked, ramp_policy_voi_regime.py defines the current-sim clean threshold-seeker and oracle controller family, degraded_regime_final.py defines the degraded-sensing framing and per-cell tau recalibration requirement
- blocked_by: Full E2 verdict remains unregistered until M3251 passes, E3 remains separate after E2 disposition, Track F remains blocked on Track E plus CP-3 regardless of M3251
- supersedes: treating the current-sim two-regime law as Chrono-scoped without a Chrono measurement, starting Track F from E1 alone
- invalidates: interpreting M3251 quick readouts as the full E2 two-regime-law verdict, claiming self-ID or history necessity from M3251, opening Track F before full Track E and CP-3

## Success Criteria

- experiments/feasibility_audit/phase4_e2_chrono_two_regime_prereg.json exists before the quick run
- experiments/feasibility_audit/phase4_e2_chrono_two_regime_quick.json exists after the quick run
- runs/feasibility_audit/phase4_e2_chrono_two_regime/episode_rows_quick.csv includes all expected quick rows
- runs/feasibility_audit/phase4_e2_chrono_two_regime/metrics_quick.csv reports protocol_gates_passed=1 and quick_mode_is_verdict=0
- docs/m3251-phase4-e2-chrono-two-regime-smoke.md reports measured and inferred sections plus the non-verdict boundary

## Failure Criteria

- M3251 runs without preregistration
- M3251 omits the degraded spot cell
- M3251 degrades geometry or command-history channels
- M3251 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3251 admits Track F or claims a full two-regime-law verdict

## Evidence Gates

- M3251 must write the E2 preregistration before any quick rollout
- M3251 must require the E0 expressibility artifact and E1 full artifact
- M3251 must write oracle_ramp, threshold_seeker, and fixed_ramp rows
- M3251 must exercise both clean reveal tiers and the delay25_tight degraded spot
- M3251 must keep geometry and command-history channels undegraded in its policy-observation filter
- M3251 must report reset finite and Chrono variant-match gates
- M3251 must label quick mode as non-verdict and keep Track F blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat M3251 as the full E2 verdict
- do not tune criteria after quick rows are observed
- do not edit ActiveSafetyReflexDriver
- do not invoke PPO, supervised training, or guarded RL
- do not degrade geometry channels or command-history channels in the E2 spot filter
- do not admit Track F from M3251

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

None recorded.
