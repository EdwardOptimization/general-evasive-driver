# m1276-paper-route-four-wheel-source-intervention-materialization-design Research Review

## Summary

- Generated at UTC: 20260528T130047Z
- Type: gate
- Gate tier: process
- Promotion decision: four_wheel_source_intervention_materialization_design_admit_implementation
- Decision reason: M1276 designs preferred rejected counterfactual source artifacts from M1273 corpus with clean 72-value observations and admits bounded materialization

## Hypothesis

A no-training source-to-intervention design can convert M1273 source-corpus rows into preferred/rejected counterfactual artifacts without actor-input leakage.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1275-paper-route-fidelity-fault-source-synthesis.md, runs/m1273_four_wheel_source_corpus_export/near_boundary_source_rows.csv, runs/m1273_four_wheel_source_corpus_export/high_regret_source_rows.csv, runs/m1273_four_wheel_source_corpus_export/family_balanced_source_rows.csv
- parent_config: experiments/manifests/m1275-paper-route-fidelity-fault-source-synthesis.json
- parent_objective: design source-to-intervention materialization from the four-wheel source corpus
- derived_from: m1275-paper-route-fidelity-fault-source-synthesis
- blocked_by: M1275 promotes the fidelity source branch to source-to-intervention/materialization
- supersedes: direct actor/Gym integration from M1273 source corpus
- invalidates: None

## Success Criteria

- docs/m1276-paper-route-four-wheel-source-intervention-materialization-design.md exists
- design specifies intervention row schema
- design specifies subset priorities
- design specifies preferred/rejected branch/action/outcome semantics
- design preserves actor-input and source-acceptance guardrails
- design pre-registers one bounded implementation if admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design leaks fault/per-wheel metadata into actor observations
- design treats source rows as driver performance
- design skips directly to actor/Gym integration
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1276 must preserve actor input contract
- M1276 must not train controllers
- M1276 must not run PPO
- M1276 must not use private holdout
- M1276 must not promote
- M1276 must design source-to-intervention artifacts before implementation

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add per-wheel/fault labels to actor inputs
- do not lower accepted-source thresholds
- do not count source rows as driver performance
- do not claim high-fidelity validation from the compact pilot

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1276-paper-route-four-wheel-source-intervention-materialization-design
- type: gate
- checkpoint: docs/m1276-paper-route-four-wheel-source-intervention-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_intervention_materialization_design_admit_implementation
- reason: M1276 designs preferred rejected counterfactual source artifacts from M1273 corpus with clean 72-value observations and admits bounded materialization

## Next Blocker

m1277-paper-route-four-wheel-source-intervention-materialization
