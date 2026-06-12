# m3231-d1b-chrono-native-oracle-pricing-full Research Review

## Summary

- Generated at UTC: 20260612T061447Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: manual_review
- Decision reason: no structured gates defined

## Hypothesis

A frozen D1b Chrono-native oracle pricing full rollout can decide whether native structured-plus-CEM oracle search preserves the C5-prime structural-ceiling direction over the preregistered Sedan/BMW Chrono variants before training validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/roadmap-phase3-codex-execution.md, docs/current-status.md, docs/m3227-d1-s4-hf-lite-chrono-pricing.md, docs/m3230-d1b-chrono-native-oracle-pricing-smoke.md
- parent_dataset: runs/feasibility_audit/c5prime_target_consolidation/episode_rows.csv, experiments/feasibility_audit/chrono_native_oracle_pricing_prereg.json
- parent_config: scripts/feasibility_audit/chrono_native_oracle_pricing.py, scripts/feasibility_audit/chrono_backend_worker.py, src/autodrift/chrono_vehicle_backend.py
- parent_objective: execute roadmap D1b after M3230 proved the native Chrono oracle-search protocol
- derived_from: M3222 A3 C5-prime target consolidation, M3227 D1 tail-replay proxy reversal, M3230 D1b Chrono-native oracle protocol smoke
- blocked_by: C3 remains blocked on C2 and PI CP-2 after M3231 satisfied the D1b direction-positive precondition
- supersedes: the D1b OPEN status line in the Phase-3 roadmap and current-status ledger
- invalidates: using M3230 quick mode as a D1b direction verdict, starting C3 before C2 succeeds and PI CP-2 approves the staged scale-up budget

## Success Criteria

- experiments/feasibility_audit/chrono_native_oracle_pricing.json exists with protocol d1b_chrono_native_oracle_pricing
- full result reports per-variant direction verdicts for sedan_tmeasy and bmw_e90_tmeasy
- the result document separates measured artifacts from inferred interpretation and states whether D1b direction-positive was satisfied

## Failure Criteria

- full rollout runs without the frozen D1b preregistration
- any requested Chrono variant fails backend_info variant matching
- native_oracle is not compared against same-row v4_pertuned
- the milestone mutates ActiveSafetyReflexDriver, trains a policy, changes Chrono mappings, or claims high-fidelity sufficiency

## Evidence Gates

- M3231 must use the frozen D1b preregistration produced before M3230 quick rollout
- M3231 must run the full selected 9-row panel on sedan_tmeasy and bmw_e90_tmeasy
- M3231 must compare native_oracle against the same-row v4_pertuned Chrono floor
- M3231 must report one direction verdict per preregistered vehicle
- M3231 must state absolute success rates are context only and not high-fidelity sufficiency claims
- M3231 must not train, mutate ActiveSafetyReflexDriver, or change Chrono backend mappings

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not touch ActiveSafetyReflexDriver
- do not train RL or create policy checkpoints
- do not mutate Chrono backend mappings during the full pricing rollout
- do not claim high-fidelity sufficiency or driver performance from D1b
- do not reinterpret absolute Chrono success rates as validation or ranking evidence
- do not proceed to C3 unless D1b is direction-positive, C2 is complete, and CP-2 approves

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3231-d1b-chrono-native-oracle-pricing-full
- type: infrastructure
- checkpoint: experiments/feasibility_audit/chrono_native_oracle_pricing.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: manual_review
- reason: no structured gates defined

## Next Blocker

C3 remains blocked until C2 succeeds and PI CP-2 adjudicates the budget/staged scale-up; D1b direction-positive is satisfied by M3231.
