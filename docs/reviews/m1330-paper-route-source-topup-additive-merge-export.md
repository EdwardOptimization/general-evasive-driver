# m1330-paper-route-source-topup-additive-merge-export Research Review

## Summary

- Generated at UTC: 20260528T180227Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_topup_additive_merge_export_pass_route_to_expansion_plan
- Decision reason: M1330 exports 366 source-identified rows and 250 family-balanced rows with no source identity duplicates while retaining global friction and halfshaft blockers

## Hypothesis

A no-policy merge/export implementation can combine M1322 and M1327 into a source-run-identified corpus with enough balanced rows for a fresh expansion plan.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1329-paper-route-source-topup-additive-merge-export-design.md, runs/m1322_source_repair_corpus_export/all_accepted_source_rows.csv, runs/m1327_source_repair_topup_horizon_corrected_smoke/accepted_separable_pairs.csv
- parent_config: experiments/manifests/m1329-paper-route-source-topup-additive-merge-export-design.json
- parent_objective: implement additive merge/export for M1322 and M1327 source rows
- derived_from: m1329-paper-route-source-topup-additive-merge-export-design
- blocked_by: M1329 admits one no-policy merge/export implementation before corpus expansion planning
- supersedes: manual naive additive source count
- invalidates: None

## Success Criteria

- focused tests pass
- runs/m1330_source_topup_additive_merge_export/summary.json exists
- source_identity_duplicate_count == 0
- merged_source_identity_rows >= 300
- family_balanced_rows >= 240
- accepted_fault_family_pairs >= 7
- global friction is reported as missing
- halfshaft undercoverage is reported
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- focused tests fail
- run artifacts are missing
- source identity duplicates are present
- family_balanced_rows < 240 without clear blocker
- global friction or halfshaft blockers are hidden
- training, PPO, private holdout, promotion, threshold relaxation, materialization, or actor-input expansion occurs

## Evidence Gates

- M1330 must not train
- M1330 must not run PPO
- M1330 must not use private holdout
- M1330 must not promote
- M1330 must preserve actor input contract
- M1330 must use source-run-prefixed identity
- M1330 must report duplicate diagnostics
- M1330 must keep halfshaft and global friction blockers explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not silently drop semantic duplicates
- do not materialize histories
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1330-paper-route-source-topup-additive-merge-export
- type: infrastructure
- checkpoint: runs/m1330_source_topup_additive_merge_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_additive_merge_export_pass_route_to_expansion_plan
- reason: M1330 exports 366 source-identified rows and 250 family-balanced rows with no source identity duplicates while retaining global friction and halfshaft blockers

## Next Blocker

m1331-paper-route-source-topup-merged-corpus-expansion-plan
