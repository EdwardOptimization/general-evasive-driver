# m1331-paper-route-source-topup-merged-corpus-expansion-plan Research Review

## Summary

- Generated at UTC: 20260528T180603Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: source_topup_merged_corpus_expansion_plan_admissible_route_to_materialization_design
- Decision reason: M1331 plans 366 source pairs and 732 groups with max fold share 0.274 while retaining global friction and halfshaft blockers

## Hypothesis

The M1330 merged source export can support an admissible source-history corpus expansion plan without stale materialized-history matches.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1330-paper-route-source-topup-additive-merge-export.md, runs/m1330_source_topup_additive_merge_export/summary.json
- parent_config: experiments/manifests/m1330-paper-route-source-topup-additive-merge-export.json
- parent_objective: run source-history corpus expansion plan on the M1330 merged source export
- derived_from: m1330-paper-route-source-topup-additive-merge-export
- blocked_by: M1330 exports a merged source corpus candidate that needs fold planning before materialization
- supersedes: source-history materialization from M1322 or M1327 alone
- invalidates: None

## Success Criteria

- runs/m1331_source_topup_merged_corpus_expansion_plan/summary.json exists
- planned_source_pairs >= 240
- planned_pair_probe_groups >= 480
- source_fault_family_count >= 7
- pair_disjoint is true
- all_folds_nonempty is true
- materialized_source_pair_count == 0
- global friction and halfshaft coverage gaps are reported
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- run artifacts are missing
- stale materialized histories are counted
- target source pairs or groups are under target without clear blocker
- folds are empty or pair-disjointness is violated
- global friction or halfshaft gaps are hidden
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1331 must not train
- M1331 must not run PPO
- M1331 must not use private holdout
- M1331 must not promote
- M1331 must preserve actor input contract
- M1331 must use the M1330 merged export
- M1331 must not count stale materialized histories
- M1331 must report global friction and halfshaft coverage gaps

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not use stale M1280 materialized history by pair id
- do not hide global friction gap
- do not hide halfshaft undercoverage
- do not route directly to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1331-paper-route-source-topup-merged-corpus-expansion-plan
- type: infrastructure
- checkpoint: runs/m1331_source_topup_merged_corpus_expansion_plan/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_topup_merged_corpus_expansion_plan_admissible_route_to_materialization_design
- reason: M1331 plans 366 source pairs and 732 groups with max fold share 0.274 while retaining global friction and halfshaft blockers

## Next Blocker

m1332-paper-route-source-topup-materialization-design
