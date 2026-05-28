# m1261-paper-route-richer-fault-regret-boundary-retarget-design Research Review

## Summary

- Generated at UTC: 20260528T114949Z
- Type: gate
- Gate tier: process
- Promotion decision: regret_boundary_retarget_design_admit_bounded_implementation_smoke
- Decision reason: M1261 designs fixed-action geometry retargeting around M1259 pair 5 to amplify two-sided cross-regret while preserving strict own-branch viability

## Hypothesis

M1259's viable action-divergent low-regret pair can motivate a bounded retargeting design that targets two-sided cross-regret rather than only viability.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1260-paper-route-richer-fault-capability-source-result-audit.md, docs/m1259-paper-route-richer-fault-capability-source-smoke.md, runs/m1259_richer_fault_capability_source_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1260-paper-route-richer-fault-capability-source-result-audit.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design a regret-boundary retargeting source repair around viable action-divergent low-regret rows
- derived_from: m1260-paper-route-richer-fault-capability-source-result-audit
- blocked_by: M1260 classifies M1259 pair 5 as viable action-divergent low-regret
- supersedes: another unstructured richer-fault source run
- invalidates: None

## Success Criteria

- docs/m1261-paper-route-richer-fault-regret-boundary-retarget-design.md exists
- design cites M1259 pair 5 metrics
- design preserves strict accepted-source criteria
- design identifies anti-collision-dominance checks
- design admits or rejects one bounded no-training smoke
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design ignores M1260 strict negative audit
- design lowers thresholds
- design targets only viability and not regret
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1261 must preserve actor input contract
- M1261 must not train controllers
- M1261 must not run PPO
- M1261 must not use private holdout
- M1261 must not promote
- M1261 must preserve strict accepted-source criteria
- M1261 must design a bounded retargeting run or reject it

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden parameters, fault labels, oracle outcomes, or search outputs to actor inputs
- do not lower min_cross_regret_margin
- do not accept negative own-branch margins
- do not treat asymmetric_success_drop as strict accepted source-positive
- do not claim current single-track proxies are true single-wheel or per-wheel faults

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1261-paper-route-richer-fault-regret-boundary-retarget-design
- type: gate
- checkpoint: docs/m1261-paper-route-richer-fault-regret-boundary-retarget-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: regret_boundary_retarget_design_admit_bounded_implementation_smoke
- reason: M1261 designs fixed-action geometry retargeting around M1259 pair 5 to amplify two-sided cross-regret while preserving strict own-branch viability

## Next Blocker

m1262-paper-route-richer-fault-regret-boundary-retarget-implementation
