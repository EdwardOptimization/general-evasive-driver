# m1314-paper-route-source-history-corpus-expansion-design Research Review

## Summary

- Generated at UTC: 20260528T162547Z
- Type: gate
- Gate tier: process
- Promotion decision: source_history_corpus_expansion_design_admit_plan_builder
- Decision reason: M1314 designs expanded source-history corpus targets and admits deterministic no-policy plan builder before more objective tuning

## Hypothesis

A larger and more source-diverse response-history corpus is needed before further source-history objective tuning can produce repeat-robust evidence.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1313-paper-route-source-history-robust-minfold-result-audit.md, runs/m1312_source_history_robust_minfold_probe/summary.json, runs/m1312_source_history_robust_minfold_tradeoff_audit/summary.json, runs/m1280_four_wheel_source_response_history_materialization/summary.json, runs/m1277_four_wheel_source_intervention_materialization/summary.json
- parent_config: experiments/manifests/m1313-paper-route-source-history-robust-minfold-result-audit.json
- parent_objective: design source-history corpus expansion after fixed-corpus pass-surface swapping
- derived_from: m1313-paper-route-source-history-robust-minfold-result-audit
- blocked_by: M1313 pivots from objective tuning to source-history corpus expansion
- supersedes: additional scalar objective tuning on the M1280/M1277 source-history corpus
- invalidates: None

## Success Criteria

- docs/m1314-paper-route-source-history-corpus-expansion-design.md exists
- design lists source fault families and scenario axes
- design defines pair-disjoint fold and corpus size targets
- design defines no-privileged-input materialization rules
- design pre-registers a no-policy plan builder if implementation is admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design repeats only current corpus axes
- design omits pair-disjoint folds
- design adds privileged actor inputs
- design routes directly to PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1314 must not train
- M1314 must not run PPO
- M1314 must not use private holdout
- M1314 must not promote
- M1314 must preserve actor input contract
- M1314 must define source-history expansion axes
- M1314 must define corpus acceptance criteria
- M1314 must define fold and holdout discipline for expanded corpus

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not tune the same 76 groups again without corpus expansion
- do not include privileged labels in actor observations
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m1314-paper-route-source-history-corpus-expansion-design
- type: gate
- checkpoint: docs/m1314-paper-route-source-history-corpus-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_history_corpus_expansion_design_admit_plan_builder
- reason: M1314 designs expanded source-history corpus targets and admits deterministic no-policy plan builder before more objective tuning

## Next Blocker

m1315-paper-route-source-history-corpus-expansion-plan
