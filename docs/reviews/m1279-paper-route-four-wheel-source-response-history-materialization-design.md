# m1279-paper-route-four-wheel-source-response-history-materialization-design Research Review

## Summary

- Generated at UTC: 20260528T131328Z
- Type: gate
- Gate tier: process
- Promotion decision: four_wheel_source_response_history_materialization_design_admit_implementation
- Decision reason: M1279 designs branch-specific response-history artifacts and same-pair wrong-history swaps before policy-side use

## Hypothesis

A no-training response-history materialization design can make M1277 preferred/rejected intervention artifacts usable for later recurrent-policy tests without revealing branch labels.

## Lineage

- parent_checkpoint: not_applicable_no_checkpoint
- parent_dataset: docs/m1278-paper-route-four-wheel-source-intervention-materialization-result-audit.md, runs/m1277_four_wheel_source_intervention_materialization/intervention_rows.csv, runs/m1277_four_wheel_source_intervention_materialization/intervention_observations.csv
- parent_config: experiments/manifests/m1278-paper-route-four-wheel-source-intervention-materialization-result-audit.json
- parent_objective: design branch-specific response-history materialization for source interventions
- derived_from: m1278-paper-route-four-wheel-source-intervention-materialization-result-audit
- blocked_by: M1278 blocks direct policy training from contradictory current-observation intervention labels
- supersedes: direct BC or actor training from M1277 current-frame intervention rows
- invalidates: None

## Success Criteria

- docs/m1279-paper-route-four-wheel-source-response-history-materialization-design.md exists
- design explains why direct current-frame training is blocked
- design specifies history prefix and frame schema
- design specifies wrong-history pair semantics
- design preserves actor-input guardrails
- design pre-registers one bounded implementation if admitted
- no training, PPO, promotion, private holdout, threshold relaxation, or actor-input expansion occurs

## Failure Criteria

- design is missing
- design ignores contradictory current-frame labels
- design leaks branch/fault labels into actor-view history
- design skips directly to actor training
- training, PPO, private holdout, promotion, threshold relaxation, or actor-input expansion occurs

## Evidence Gates

- M1279 must preserve actor input contract
- M1279 must not train controllers
- M1279 must not run PPO
- M1279 must not use private holdout
- M1279 must not promote
- M1279 must design branch-specific response-history artifacts without actor-input leakage

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add fault labels or branch labels to actor observations
- do not lower accepted-source thresholds
- do not train directly on contradictory current-frame intervention rows
- do not claim self-identification from source artifacts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1279-paper-route-four-wheel-source-response-history-materialization-design
- type: gate
- checkpoint: docs/m1279-paper-route-four-wheel-source-response-history-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: four_wheel_source_response_history_materialization_design_admit_implementation
- reason: M1279 designs branch-specific response-history artifacts and same-pair wrong-history swaps before policy-side use

## Next Blocker

m1280-paper-route-four-wheel-source-response-history-materialization
