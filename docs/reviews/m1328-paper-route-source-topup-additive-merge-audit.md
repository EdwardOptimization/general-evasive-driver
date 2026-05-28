# m1328-paper-route-source-topup-additive-merge-audit Research Review

## Summary

- Generated at UTC: 20260528T175150Z
- Type: gate
- Gate tier: process
- Promotion decision: source_topup_additive_merge_audit_admit_merge_export_design
- Decision reason: M1328 audits M1327 as additive top-up over M1322 and admits merge/export design with halfshaft and global friction blockers explicit

## Hypothesis

M1327 is better used as an additive top-up over M1322 than as a replacement corpus, but this must be audited before export or materialization.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1327-paper-route-source-repair-topup-horizon-corrected-smoke.md, runs/m1327_source_repair_topup_horizon_corrected_smoke/summary.json, runs/m1322_source_repair_corpus_export/summary.json
- parent_config: experiments/manifests/m1327-paper-route-source-repair-topup-horizon-corrected-smoke.json
- parent_objective: audit whether M1322 and M1327 should be merged as an additive source corpus
- derived_from: m1327-paper-route-source-repair-topup-horizon-corrected-smoke
- blocked_by: M1327 is source-positive but under target as a standalone replacement and halfshaft/global friction remain inactive
- supersedes: direct materialization from M1327 alone
- invalidates: None

## Success Criteria

- docs/m1328-paper-route-source-topup-additive-merge-audit.md exists
- audit compares M1322 and M1327 family counts
- audit states naive additive total and its limitations
- audit keeps global friction and halfshaft blockers explicit
- audit chooses merge/export, further repair, or merge-preview route
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- audit document is missing
- audit treats naive additive counts as final merged counts
- audit hides halfshaft or global friction blockers
- audit routes directly to PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1328 must not train
- M1328 must not run PPO
- M1328 must not use private holdout
- M1328 must not promote
- M1328 must preserve actor input contract
- M1328 must not use naive additive counts as final merged counts
- M1328 must keep global friction and halfshaft blockers explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not treat M1327 alone as a replacement corpus
- do not claim merged corpus readiness without dedupe or identity audit
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1328-paper-route-source-topup-additive-merge-audit
- type: gate
- checkpoint: docs/m1328-paper-route-source-topup-additive-merge-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_additive_merge_audit_admit_merge_export_design
- reason: M1328 audits M1327 as additive top-up over M1322 and admits merge/export design with halfshaft and global friction blockers explicit

## Next Blocker

m1329-paper-route-source-topup-additive-merge-export-design
