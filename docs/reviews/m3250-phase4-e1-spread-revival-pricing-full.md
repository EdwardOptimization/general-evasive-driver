# m3250-phase4-e1-spread-revival-pricing-full Research Review

## Summary

- Generated at UTC: 20260612T190608Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: e1_full_pricing_completed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E1 full Chrono spread-revival pricing panel can decide whether same-instance per-vehicle tuning beats a global fixed* reflex and RLS-retuned reflex across the M3248-admitted Chrono vehicle fixtures before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md, docs/m3249-phase4-e1-spread-revival-pricing-smoke.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md, docs/m3222-a3-c5prime-target-consolidation.md
- parent_dataset: experiments/feasibility_audit/chrono_spread_expressibility_audit.json, experiments/feasibility_audit/phase4_e1_spread_revival_quick.json, experiments/feasibility_audit/c5prime_target_consolidation.json, runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv
- parent_config: experiments/feasibility_audit/phase4_e1_spread_revival_full_prereg.json, scripts/feasibility_audit/phase4_e1_spread_revival_pricing_full.py, scripts/feasibility_audit/chrono_native_oracle_pricing.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: Phase-4 Track E E1: full Chrono spread-revival pricing after E0 and M3249, M3250 decides the E1 full pricing verdict under frozen selection/validation rows and paired CIs
- derived_from: M3248 admitted E1 on selected Chrono vehicle fixtures with load-transfer physics active, M3249 proved the four-arm E1 protocol executes across Sedan/BMW_E90/UAZBUS, M3231 provides reusable native Chrono oracle-search machinery, M3222 provides C5-prime T-limit source rows with enough same-instance disjoint rows for selection/validation
- blocked_by: Track F remains blocked on Track E plus CP-3 regardless of M3250 verdict, E2/E3 remain separate open Track E units after E1
- supersedes: using M3249 quick mode as an E1 spread-revival verdict, starting Track F before a full E1 verdict
- invalidates: interpreting M3250 as independent payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr coverage, starting robotics-parity RL from E1 alone without E2/E3 and CP-3, treating the attempt-limited native oracle as a full high-fidelity sufficiency proof

## Success Criteria

- experiments/feasibility_audit/phase4_e1_spread_revival_full_prereg.json exists before the full run
- experiments/feasibility_audit/phase4_e1_spread_revival_full.json exists after the full run
- runs/feasibility_audit/phase4_e1_spread_revival/episode_rows_full.csv includes selection rows and paired validation rows
- runs/feasibility_audit/phase4_e1_spread_revival/metrics_full.csv reports protocol_gates_passed=1
- docs/m3250-phase4-e1-spread-revival-pricing-full.md reports measured and inferred sections plus the frozen verdict

## Failure Criteria

- M3250 runs without a full preregistration
- M3250 uses validation rows for grid selection
- M3250 runs training or writes a policy checkpoint
- M3250 mutates ActiveSafetyReflexDriver or the incumbent driver
- M3250 admits Track F, C2/C3, driver-performance, high-fidelity sufficiency, paper, or self-ID claims

## Evidence Gates

- M3250 must load the M3248 E0 artifact and refuse a full run if E0 did not admit E1
- M3250 must require the M3249 quick protocol artifact before full pricing
- M3250 must write a full preregistration before the full run
- M3250 must use disjoint same-instance selection and validation source rows
- M3250 must choose fixed* and per-instance tuned grids only from selection rows
- M3250 must write fixed_star, v4_rls, v4_pertuned, and native_oracle validation rows for every variant/pair
- M3250 must report paired CIs and apply the frozen >=2 qualifying variants rule
- M3250 must not admit Track F, driver-performance, high-fidelity sufficiency, paper, or self-ID claims

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use validation rows for grid selection
- do not reinterpret M3249 quick rows as full pricing evidence
- do not claim payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr coverage
- do not edit ActiveSafetyReflexDriver
- do not invoke train_ppo, supervised training, PPO, or guarded RL
- do not start Track F from M3250 without completing Track E and CP-3

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3250-phase4-e1-spread-revival-pricing-full
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: e1_full_pricing_completed
- reason: all structured gates passed

## Next Blocker

None recorded.
