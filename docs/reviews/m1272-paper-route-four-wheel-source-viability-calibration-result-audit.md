# m1272-paper-route-four-wheel-source-viability-calibration-result-audit Research Review

## Summary

- Generated at UTC: 20260528T124958Z
- Type: gate
- Gate tier: process
- Promotion decision: four_wheel_source_viability_calibration_audit_admit_source_corpus_export
- Decision reason: M1272 audits M1271 as source-positive but not actor-ready and admits stratified source corpus export with boundary high-regret and family-balance subsets

## Hypothesis

The M1271 source-positive rows can be audited for source diversity and boundary usefulness before any actor/history integration.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1271-paper-route-four-wheel-source-viability-calibration-smoke.md, runs/m1271_four_wheel_source_viability_calibration_smoke/summary.json, runs/m1271_four_wheel_source_viability_calibration_smoke/accepted_separable_pairs.csv, runs/m1271_four_wheel_source_viability_calibration_smoke/matched_capability_pairs.csv
- parent_config: experiments/manifests/m1271-paper-route-four-wheel-source-viability-calibration-smoke.json
- parent_objective: audit calibrated four-wheel source-positive rows before actor/history integration
- derived_from: m1271-paper-route-four-wheel-source-viability-calibration-smoke
- blocked_by: M1271 produced accepted source rows, but source diversity and boundary usefulness must be audited before training or integration
- supersedes: direct Gym/actor integration from M1271 source-positive rows
- invalidates: None

## Success Criteria

- docs/m1272-paper-route-four-wheel-source-viability-calibration-result-audit.md exists
- audit cites M1271 accepted rows and source-diversity evidence
- audit classifies halfshaft inactivity
- audit decides whether to export corpus, filter boundary rows, retarget, or synthesize
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- audit document is missing
- audit ignores source diversity
- audit treats source-positive rows as driver performance
- audit skips directly to actor/Gym integration
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1272 must preserve actor input contract
- M1272 must not train controllers
- M1272 must not run PPO
- M1272 must not use private holdout
- M1272 must not promote
- M1272 must audit source diversity and boundary usefulness
- M1272 must decide the next source step before actor/Gym integration

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not count horizon-only rows as success
- do not claim high-fidelity validation from the compact pilot
- do not treat source-positive rows as driver performance

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1272-paper-route-four-wheel-source-viability-calibration-result-audit
- type: gate
- checkpoint: docs/m1272-paper-route-four-wheel-source-viability-calibration-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_viability_calibration_audit_admit_source_corpus_export
- reason: M1272 audits M1271 as source-positive but not actor-ready and admits stratified source corpus export with boundary high-regret and family-balance subsets

## Next Blocker

m1273-paper-route-four-wheel-source-corpus-export
