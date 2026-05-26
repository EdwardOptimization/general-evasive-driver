# m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator Research Review

## Summary

- Generated at UTC: 20260526T182837Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: margin_weighted_branch_trust_region_evaluator_pass_route_to_repair_update_design
- Decision reason: M1011 no-update evaluator passes: base trust loss 0 alpha 0.01 loss 3.5297 alpha 0.2 loss 1407.0 rows 6 and 15 contribute 66.45 percent and no actor/PPO/promotion occurs

## Hypothesis

Margin slack weighting will make the rejected-branch trust residual sensitive to alpha 0.01 on rows 6 and 15 while preserving zero base loss.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_01.pt, runs/m1002_v4_public_base_temporal_sequence_objective_update_probe/checkpoints/alpha_0_2.pt
- parent_dataset: docs/m1010-v4-public-base-margin-weighted-branch-trust-region-design.md, runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/*/boundary_replay_rows.csv, runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1010-v4-public-base-margin-weighted-branch-trust-region-design.json
- parent_objective: implement no-update margin-weighted rejected-branch trust-region evaluator
- derived_from: m1010-v4-public-base-margin-weighted-branch-trust-region-design
- blocked_by: M1010 requires evaluator calibration before any actor update
- supersedes: None
- invalidates: actor update before margin-weighted branch trust-region evaluator sanity

## Success Criteria

- summary.json exists
- M974 base trust loss is zero
- alpha 0.01 trust loss is positive
- alpha 0.20 trust loss exceeds alpha 0.01
- row 6 and row 15 dominate weighted loss
- actor parameters are unchanged
- ppo_used == false
- promoted == false

## Failure Criteria

- evaluator changes actor parameters
- margin-weighted metrics are non-finite
- alpha 0.01 is not distinguished from base
- PPO starts
- promotion occurs

## Evidence Gates

- M1011 must not train
- M1011 must not run PPO
- M1011 must not promote
- M1011 must preserve P0 actor inputs
- M1011 must show alpha 0.01 activates the margin-weighted wrong-branch trust residual

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not use private holdout
- do not run replay gates as promotion evidence
- do not change actor input contract

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1011-v4-public-base-margin-weighted-branch-trust-region-evaluator
- type: infrastructure
- checkpoint: runs/m1011_v4_public_base_margin_weighted_branch_trust_region_evaluator/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: margin_weighted_branch_trust_region_evaluator_pass_route_to_repair_update_design
- reason: M1011 no-update evaluator passes: base trust loss 0 alpha 0.01 loss 3.5297 alpha 0.2 loss 1407.0 rows 6 and 15 contribute 66.45 percent and no actor/PPO/promotion occurs

## Next Blocker

m1012-v4-public-base-margin-weighted-branch-repair-update-design
