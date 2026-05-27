# m1144-v4-public-base-row15-promoted-objective-corpus-run Research Review

## Summary

- Generated at UTC: 20260527T225602Z
- Type: objective_sanity
- Gate tier: proof
- Promotion decision: row15_promoted_objective_corpus_pass_route_to_result_audit
- Decision reason: M1144 corpus passes with 76 rows and objective sanity passes across three seeds with mean val pairwise accuracy after 1.0

## Hypothesis

The M1142 row15_current materialized rows can produce a valid single-checkpoint boundary-outcome corpus and learnable auxiliary objective.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1143-v4-public-base-row15-promoted-objective-corpus-design.md, runs/m1142_row15_promoted_target_materialization/row15_current_boundary_rows.csv
- parent_config: experiments/manifests/m1143-v4-public-base-row15-promoted-objective-corpus-design.json, configs/m121_human_view_zero_obstacle_relvel.json
- parent_objective: run row15_current single-checkpoint boundary-outcome corpus and objective sanity
- derived_from: m1143-v4-public-base-row15-promoted-objective-corpus-design
- blocked_by: M1143 pre-registers corpus and objective sanity thresholds
- supersedes: None
- invalidates: actor update before objective sanity, promotion from objective sanity alone, using non-row15_current checkpoint policies in the first M1142 corpus run

## Success Criteria

- summary.json exists
- corpus artifacts exist
- corpus_rows >= 70
- physical_pairs >= 12
- targets == 2
- success_drop_rows == corpus_rows
- selected_source_rows >= 70
- action_reconstruction_error_max <= 0.005
- action_reconstruction_error_mean <= 0.001
- objective_pass == true
- seed_pass_count == 3
- min_val_combined_loss_improvement > 0
- min_val_delta_loss_improvement > 0
- mean_val_pairwise_accuracy_after >= 0.60
- no actor training, PPO, replay, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- corpus artifact is missing
- corpus or action reconstruction gate fails
- objective sanity gate fails
- actor training, PPO, replay, mining, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1144 may build corpus and run objective sanity only
- M1144 must use row15_current checkpoint policy only
- M1144 must not train actor weights
- M1144 must not run PPO
- M1144 must not run replay
- M1144 must not mine rows
- M1144 must not promote
- M1144 must not use private holdout
- M1144 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run replay
- do not mine rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not add additional checkpoint policies
- do not weaken corpus thresholds after seeing the result

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1144-v4-public-base-row15-promoted-objective-corpus-run
- type: objective_sanity
- checkpoint: runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_objective_corpus_pass_route_to_result_audit
- reason: M1144 corpus passes with 76 rows and objective sanity passes across three seeds with mean val pairwise accuracy after 1.0

## Next Blocker

m1145-v4-public-base-row15-promoted-objective-result-audit
