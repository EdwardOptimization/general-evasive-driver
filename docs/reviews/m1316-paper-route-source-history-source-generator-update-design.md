# m1316-paper-route-source-history-source-generator-update-design Research Review

## Summary

- Generated at UTC: 20260528T163705Z
- Type: gate
- Gate tier: process
- Promotion decision: source_generator_update_design_admit_source_generation_smoke
- Decision reason: M1316 designs source generator updates and blocks fake family labels before a no-policy source-generation smoke

## Hypothesis

Source generator updates can be designed to cover the missing M1315 families while preserving human-view actor inputs and action-divergence acceptance criteria.

## Lineage

- parent_checkpoint: not_applicable
- parent_dataset: docs/m1315-paper-route-source-history-corpus-expansion-plan.md, runs/m1315_source_history_corpus_expansion_plan/summary.json, runs/m1315_source_history_corpus_expansion_plan/requires_source_generator_update.csv
- parent_config: experiments/manifests/m1315-paper-route-source-history-corpus-expansion-plan.json
- parent_objective: design source generator updates for missing and undercovered source-history families
- derived_from: m1315-paper-route-source-history-corpus-expansion-plan
- blocked_by: M1315 reports source-history coverage gaps and under-target family coverage
- supersedes: materializing M1315's current 108-pair plan as the expanded corpus
- invalidates: None

## Success Criteria

- docs/m1316-paper-route-source-history-source-generator-update-design.md exists
- design lists supported and blocked source families
- design defines action-divergence and margin acceptance criteria
- design defines no-policy smoke implementation route
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design document is missing
- design relabels unsupported families without dynamics
- design omits acceptance criteria
- design routes directly to PPO
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1316 must not train
- M1316 must not run PPO
- M1316 must not use private holdout
- M1316 must not promote
- M1316 must preserve actor input contract
- M1316 must design generator support for missing families
- M1316 must define action-divergence acceptance criteria

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not fabricate source labels without dynamics
- do not materialize non-divergent families as accepted
- do not overclaim self-identification

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1316-paper-route-source-history-source-generator-update-design
- type: gate
- checkpoint: docs/m1316-paper-route-source-history-source-generator-update-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: source_generator_update_design_admit_source_generation_smoke
- reason: M1316 designs source generator updates and blocks fake family labels before a no-policy source-generation smoke

## Next Blocker

m1317-paper-route-source-generator-update-smoke
