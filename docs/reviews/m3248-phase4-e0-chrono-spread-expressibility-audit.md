# m3248-phase4-e0-chrono-spread-expressibility-audit Research Review

## Summary

- Generated at UTC: 20260612T173622Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: e0_passed
- Decision reason: all structured gates passed

## Hypothesis

A preregistered Phase-4 E0 Chrono spread expressibility audit can freeze the vehicle-class, mass, load-transfer, tire, and unmapped-axis envelope that E1 is allowed to price before validation ranking promotion driver-performance current-sim high-fidelity full-driver repair-success robustness-result feasibility-proof paper or self-ID claim.

## Lineage

- parent_checkpoint: docs/current-status.md, docs/roadmap-phase3-codex-execution.md, docs/m3218-s4-hf-lite-backend-inventory-preflight.md, docs/m3219-s4-hf-lite-chrono-variant-selector-smoke.md, docs/m3227-d1-s4-hf-lite-chrono-pricing.md, docs/m3231-d1b-chrono-native-oracle-pricing-full.md, docs/m3247-c1-v4-stage-b-guarded-rl.md
- parent_dataset: experiments/feasibility_audit/s4_hf_lite_backend_inventory.json, experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json, experiments/feasibility_audit/s4_hf_lite_chrono_pricing.json, experiments/feasibility_audit/chrono_native_oracle_pricing.json
- parent_config: src/autodrift/chrono_vehicle_backend.py, scripts/feasibility_audit/chrono_worker_client.py, experiments/feasibility_audit/chrono_spread_expressibility_prereg.json, experiments/feasibility_audit/chrono_spread_expressibility_quick.json
- parent_objective: Phase-4 Track E: move decisive pricing questions to Chrono before any robotics-parity RL work, E0 acceptance: frozen spread-axis table feeding E1
- derived_from: M3218 found Chrono resources but no original variant selector, M3219 added and smoked the whitelisted Sedan/BMW_E90/UAZBUS selector, M3227 and M3231 showed that Chrono-side direction pricing depends on native backend evidence rather than current-sim tail replay, M3247 closed current-sim Track C without a performance or self-ID claim
- blocked_by: E1/E2/E3 cannot be preregistered until E0 declares the expressible Chrono spread envelope, Track F remains blocked on Track E plus CP-3
- supersedes: treating M3218/M3219 as sufficient E1 expressibility without a frozen Phase-4 axis table
- invalidates: starting E1 with payload-position, h_cg, tire-family, split-mu, or continuous lf/lr/Iz/cf/cr axes under the current backend, using total-mass override as a proxy for payload-position or CG-height control

## Success Criteria

- experiments/feasibility_audit/chrono_spread_expressibility_prereg.json exists before the full E0 run
- experiments/feasibility_audit/chrono_spread_expressibility_quick.json exists before full interpretation
- experiments/feasibility_audit/chrono_spread_expressibility_audit.json exists after the full run
- runs/feasibility_audit/chrono_spread_expressibility/variant_reset_rows.csv records all three full variants
- runs/feasibility_audit/chrono_spread_expressibility/metrics.csv reports status_pass=1 and e1_preregistration_admitted=1
- docs/m3248-phase4-e0-chrono-spread-expressibility-audit.md separates measured reset/step evidence from inferred E1 envelope limits

## Failure Criteria

- a full E0 variant fails reset/step, obs72 finite, or variant-match gates
- payload-position or CG-height is admitted without a backend connector
- E0 quick mode is used as the final E1 admission artifact
- M3248 edits or mutates ActiveSafetyReflexDriver
- M3248 makes a driver-performance, high-fidelity sufficiency, paper, repair-success, feasibility-proof, robustness, or self-ID claim

## Evidence Gates

- M3248 must write a preregistration before the full E0 run
- M3248 must reset/step all full E0 Chrono variants with finite obs72 and matching backend_info variant ids
- M3248 must freeze an axis table with control_class, current_status, mechanism, E1 use, evidence, and forbidden interpretation
- M3248 must explicitly block payload-position or CG-height control unless a new connector exists
- M3248 must distinguish selected Chrono fixture load-transfer physics from an independent h_cg or payload sweep
- M3248 must not mutate ActiveSafetyReflexDriver or make any driver-performance, high-fidelity sufficiency, paper, or self-ID claim

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not start E1 pricing before the full E0 artifact exists
- do not treat Chrono resource availability as wired tire-family control
- do not treat total-mass override as payload-position or CG-height control
- do not add or edit ActiveSafetyReflexDriver
- do not use E0 quick mode as the E1 admission artifact
- do not claim a learned-policy, driver-performance, high-fidelity sufficiency, repair-success, or self-ID result

## Failure Taxonomy

- none

## Scoreboard

- milestone: m3248-phase4-e0-chrono-spread-expressibility-audit
- type: infrastructure
- checkpoint: None
- success_rate: 1
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: e0_passed
- reason: all structured gates passed

## Next Blocker

None recorded.
