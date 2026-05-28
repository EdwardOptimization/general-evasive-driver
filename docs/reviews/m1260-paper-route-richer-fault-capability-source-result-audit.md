# m1260-paper-route-richer-fault-capability-source-result-audit Research Review

## Summary

- Generated at UTC: 20260528T114547Z
- Type: gate
- Gate tier: process
- Promotion decision: richer_fault_source_low_regret_audit_admit_regret_boundary_retarget_design
- Decision reason: M1260 audits M1259 as strict source-negative with viable action-divergent low-regret pair 5 and admits one regret-boundary retarget design before another source run

## Hypothesis

M1259's richer-fault source result should be audited as strict source-negative with a useful low-regret near-miss, not treated as source-positive.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1259-paper-route-richer-fault-capability-source-smoke.md, runs/m1259_richer_fault_capability_source_smoke/summary.json, runs/m1259_richer_fault_capability_source_smoke/matched_capability_pairs.csv, runs/m1259_richer_fault_capability_source_smoke/fault_family_pair_summary.csv
- parent_config: experiments/manifests/m1259-paper-route-richer-fault-capability-source-smoke.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: audit richer-fault source result after strict accepted-source rerun remains zero-accepted
- derived_from: m1259-paper-route-richer-fault-capability-source-smoke
- blocked_by: M1259 produced stronger action-divergent low-regret evidence but strict accepted separable pairs remained zero
- supersedes: another immediate richer-fault source run without auditing the strict negative and metric correction
- invalidates: None

## Success Criteria

- docs/m1260-paper-route-richer-fault-capability-source-result-audit.md exists
- audit cites M1259 strict accepted_separable_pairs and result_class
- audit records the asymmetric_success_drop acceptance correction
- audit classifies pair 5 and the dominant row patterns
- audit does not lower thresholds
- audit chooses the next branch decision
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- audit is missing
- audit ignores strict acceptance correction
- audit treats M1259 as source-positive
- audit proposes another source run without a new evidence variable
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1260 must preserve actor input contract
- M1260 must not train controllers
- M1260 must not run PPO
- M1260 must not use private holdout
- M1260 must not promote
- M1260 must preserve strict accepted-source criteria
- M1260 must decide whether to try one bounded richer-fault repair variable, synthesize, or pivot

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

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m1260-paper-route-richer-fault-capability-source-result-audit
- type: gate
- checkpoint: docs/m1260-paper-route-richer-fault-capability-source-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: richer_fault_source_low_regret_audit_admit_regret_boundary_retarget_design
- reason: M1260 audits M1259 as strict source-negative with viable action-divergent low-regret pair 5 and admits one regret-boundary retarget design before another source run

## Next Blocker

m1261-paper-route-richer-fault-regret-boundary-retarget-design
