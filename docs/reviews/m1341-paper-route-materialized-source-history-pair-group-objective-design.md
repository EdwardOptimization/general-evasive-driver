# m1341-paper-route-materialized-source-history-pair-group-objective-design Research Review

## Summary

- Generated at UTC: 20260528T185453Z
- Type: gate
- Gate tier: process
- Promotion decision: materialized_source_history_pair_group_objective_design_admit_group_metric_evaluator
- Decision reason: M1341 designs group-min pair objective over 688 source_identity/probe groups and admits no-update group metrics

## Hypothesis

The M1340 two-condition conflict can be addressed by designing a group-level objective that treats source_identity/probe_template pairs as the unit of work before any actor update.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1340-paper-route-materialized-source-history-objective-evaluator-result-audit.md, runs/m1339_materialized_source_history_objective_evaluator/materialized_source_history_objective_rows.csv, runs/m1339_materialized_source_history_objective_evaluator/family_summary.csv, runs/m1339_materialized_source_history_objective_evaluator/fold_summary.csv
- parent_config: experiments/manifests/m1340-paper-route-materialized-source-history-objective-evaluator-result-audit.json
- parent_objective: design pair/group objective after M1340 classifies two-condition directional conflict
- derived_from: m1340-paper-route-materialized-source-history-objective-evaluator-result-audit
- blocked_by: M1340 shows rowwise M1339 exact objective has balanced one-sided two-condition conflict
- supersedes: direct rowwise source-history objective update from M1339
- invalidates: None

## Success Criteria

- docs/m1341-paper-route-materialized-source-history-pair-group-objective-design.md exists
- design specifies group keys and expected group counts
- design specifies group-min or lexicographic directional terms
- design specifies anti-overfit guards against solving one condition only
- design specifies exact no-update group evaluator or bounded implementation route
- no training, PPO, promotion, private holdout, threshold relaxation, actor update, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- group semantics are ambiguous
- design ignores the two-condition conflict
- design routes directly to PPO or actor update
- training, PPO, private holdout, promotion, threshold relaxation, actor update, or actor-input expansion occurs

## Evidence Gates

- M1341 must not train
- M1341 must not run PPO
- M1341 must not update actor weights
- M1341 must not use private holdout
- M1341 must not promote
- M1341 must preserve actor input contract
- M1341 must design group-level objective semantics
- M1341 must preserve both condition rows inside each group

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor weights
- do not promote
- do not use private holdout
- do not add actor inputs
- do not use pair-specific tuning to hide conflict
- do not claim self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1341-paper-route-materialized-source-history-pair-group-objective-design
- type: gate
- checkpoint: docs/m1341-paper-route-materialized-source-history-pair-group-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: materialized_source_history_pair_group_objective_design_admit_group_metric_evaluator
- reason: M1341 designs group-min pair objective over 688 source_identity/probe groups and admits no-update group metrics

## Next Blocker

m1342-paper-route-materialized-source-history-pair-group-metric-evaluator
