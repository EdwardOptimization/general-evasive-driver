# m1258-paper-route-richer-fault-capability-source-design Research Review

## Summary

- Generated at UTC: 20260528T112921Z
- Type: gate
- Gate tier: process
- Promotion decision: richer_fault_capability_source_design_admit_bounded_v4_proxy_fault_smoke
- Decision reason: M1258 designs richer v4 proxy-fault source-family smoke with unchanged capability-separable thresholds and high-fidelity per-wheel fault claims blocked

## Hypothesis

A richer fault/source-family branch using the existing v4 proxy-fault configuration is the next clean evidence variable after local source construction failed.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1257-paper-route-capability-separable-source-construction-synthesis.md, docs/m1256-paper-route-capability-separable-event-timing-source-result-audit.md, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_config: experiments/manifests/m1257-paper-route-capability-separable-source-construction-synthesis.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: design a richer fault/source-family capability-separable source branch after M1257 closes the local source-construction branch
- derived_from: m1257-paper-route-capability-separable-source-construction-synthesis
- blocked_by: M1257 identifies capability_separable_source_family_gap in the current source branch
- supersedes: another local timing/proposal/relocation source tweak
- invalidates: None

## Success Criteria

- docs/m1258-paper-route-richer-fault-capability-source-design.md exists
- design cites M1257 synthesis
- design identifies whether the existing v4 config can be used for a bounded smoke
- design preserves capability-separable thresholds
- design preserves proxy/high-fidelity claim boundaries
- no training, PPO, promotion, private holdout, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design repeats a local timing/proposal/relocation tweak as the main change
- design blurs current-model proxy faults with true per-wheel/high-fidelity faults
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1258 must preserve actor input contract
- M1258 must not train controllers
- M1258 must not run PPO
- M1258 must not use private holdout
- M1258 must not promote
- M1258 must keep proxy fault claims separate from true four-wheel/high-fidelity fault claims
- M1258 must pre-register any later run with unchanged capability-separable thresholds

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
- do not claim current single-track proxies are true single-wheel or per-wheel faults

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1258-paper-route-richer-fault-capability-source-design
- type: gate
- checkpoint: docs/m1258-paper-route-richer-fault-capability-source-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: richer_fault_capability_source_design_admit_bounded_v4_proxy_fault_smoke
- reason: M1258 designs richer v4 proxy-fault source-family smoke with unchanged capability-separable thresholds and high-fidelity per-wheel fault claims blocked

## Next Blocker

m1259-paper-route-richer-fault-capability-source-smoke
