# m1332-paper-route-source-topup-materialization-design Research Review

## Summary

- Generated at UTC: 20260528T181313Z
- Type: gate
- Gate tier: process
- Promotion decision: source_topup_materialization_design_admit_implementation
- Decision reason: M1332 designs source-run identity preserving no-policy response-history materialization for 366 pairs with expected 1464 prefixes and 35136 frame rows

## Hypothesis

The M1330/M1331 merged source corpus can be materialized into command-response histories while preserving source identity metadata.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1331-paper-route-source-topup-merged-corpus-expansion-plan.md, runs/m1331_source_topup_merged_corpus_expansion_plan/summary.json, runs/m1330_source_topup_additive_merge_export/summary.json
- parent_config: experiments/manifests/m1331-paper-route-source-topup-merged-corpus-expansion-plan.json
- parent_objective: design source-history materialization from the M1330 merged source export
- derived_from: m1331-paper-route-source-topup-merged-corpus-expansion-plan
- blocked_by: M1331 admits source-history materialization design but materialized artifacts do not yet exist
- supersedes: materializing the old M1273 or M1322 source corpus
- invalidates: None

## Success Criteria

- docs/m1332-paper-route-source-topup-materialization-design.md exists
- design specifies M1330 and M1331 input artifacts
- design preserves source_run_id, source_row_id, and original_pair_id
- design lists materialization output artifacts
- design routes to one no-policy materialization implementation
- no training, PPO, promotion, private holdout, threshold relaxation, materialization run, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design drops source identity metadata
- design hides global friction or halfshaft blockers
- design routes directly to policy objective or PPO
- training, PPO, private holdout, promotion, threshold relaxation, materialization run, or actor-input expansion occurs

## Evidence Gates

- M1332 must not train
- M1332 must not run PPO
- M1332 must not use private holdout
- M1332 must not promote
- M1332 must preserve actor input contract
- M1332 must preserve source identity metadata
- M1332 must not materialize histories before implementation manifest
- M1332 must keep global friction and halfshaft blockers explicit

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate global friction coverage
- do not hide halfshaft undercoverage
- do not run materialization before design
- do not overclaim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1332-paper-route-source-topup-materialization-design
- type: gate
- checkpoint: docs/m1332-paper-route-source-topup-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_materialization_design_admit_implementation
- reason: M1332 designs source-run identity preserving no-policy response-history materialization for 366 pairs with expected 1464 prefixes and 35136 frame rows

## Next Blocker

m1333-paper-route-source-topup-materialization-implementation
