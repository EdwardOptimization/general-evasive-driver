# m1329-paper-route-source-topup-additive-merge-export-design Research Review

## Summary

- Generated at UTC: 20260528T175552Z
- Type: gate
- Gate tier: process
- Promotion decision: source_topup_additive_merge_export_design_admit_implementation
- Decision reason: M1329 designs source-run-identified additive merge/export with duplicate diagnostics family cap 40 and no materialization

## Hypothesis

A no-policy merge/export tool can be designed to combine M1322 and M1327 source rows with safe source identity and explicit duplicate diagnostics.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1328-paper-route-source-topup-additive-merge-audit.md, runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv, runs/m1327_source_repair_topup_horizon_corrected_smoke/accepted_separable_pairs.csv
- parent_config: experiments/manifests/m1328-paper-route-source-topup-additive-merge-audit.json
- parent_objective: design additive merge/export tool for M1322 and M1327 source rows
- derived_from: m1328-paper-route-source-topup-additive-merge-audit
- blocked_by: M1328 admits additive merge but requires explicit source identity and dedupe diagnostics before export
- supersedes: direct source-history materialization from M1322 or M1327 alone
- invalidates: None

## Success Criteria

- docs/m1329-paper-route-source-topup-additive-merge-export-design.md exists
- design specifies source_run_id and source_row_id
- design specifies semantic duplicate diagnostics
- design lists output artifacts
- design routes to one no-policy merge/export implementation
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design omits source-run-prefixed identity
- design hides halfshaft or global friction blockers
- design routes directly to materialization or PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1329 must not train
- M1329 must not run PPO
- M1329 must not use private holdout
- M1329 must not promote
- M1329 must preserve actor input contract
- M1329 must define source-run-prefixed identity
- M1329 must define semantic duplicate diagnostics
- M1329 must keep halfshaft and global friction blockers explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not export without source-run-prefixed identity
- do not silently drop semantic duplicates
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1329-paper-route-source-topup-additive-merge-export-design
- type: gate
- checkpoint: docs/m1329-paper-route-source-topup-additive-merge-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_additive_merge_export_design_admit_implementation
- reason: M1329 designs source-run-identified additive merge/export with duplicate diagnostics family cap 40 and no materialization

## Next Blocker

m1330-paper-route-source-topup-additive-merge-export
