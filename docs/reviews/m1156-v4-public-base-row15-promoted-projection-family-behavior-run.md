# m1156-v4-public-base-row15-promoted-projection-family-behavior-run Research Review

## Summary

- Generated at UTC: 20260527T235809Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_promoted_projection_expanded_diagnostic_pass_route_to_result_audit
- Decision reason: M1156 alpha_0_05 keeps M1144 exact delta -0.000378 and passes exact proof old-public replay family-intersection source-diverse fresh/OOD and behavior diagnostics with no training PPO promotion private holdout or actor-input change

## Hypothesis

The M1154 alpha_0_05 candidate preserves M1144 exact objective and passes expanded public proof, family-intersection, generalization, and behavior diagnostics.

## Lineage

- parent_checkpoint: runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m1155-v4-public-base-row15-promoted-projection-family-behavior-design.md, runs/m1154_row15_promoted_unsafe_margin_projection_probe/summary.json
- parent_config: experiments/manifests/m1155-v4-public-base-row15-promoted-projection-family-behavior-design.json
- parent_objective: run M1144 exact recheck and expanded public diagnostic wrapper for alpha_0_05
- derived_from: m1155-v4-public-base-row15-promoted-projection-family-behavior-design
- blocked_by: M1155 designs diagnostics after M1154 first replay candidate
- supersedes: None
- invalidates: promotion before expanded diagnostics, PPO before expanded diagnostics, private holdout before public diagnostics

## Success Criteria

- M1144 exact recheck summary exists
- expanded public diagnostic summary exists
- M1144 exact delta remains negative
- expanded wrapper result_class is candidate_b_combined_active_set_full_public_gate_candidate
- family_intersection_pass is true
- behavior_pass is true
- promotion remains blocked
- no actor training, PPO, mining, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- M1144 exact recheck fails
- expanded wrapper summary is missing after exact pass
- any expanded public diagnostic tier fails
- promotion is attempted
- actor training, PPO, mining, private holdout, or actor-input change starts

## Evidence Gates

- M1156 may run M1144 exact recheck and expanded public diagnostic wrapper only
- M1156 must not train actor weights
- M1156 must not run PPO
- M1156 must not mine new rows
- M1156 must not promote
- M1156 must not use private holdout
- M1156 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not mine new rows
- do not promote
- do not use private holdout
- do not change actor inputs
- do not run expanded wrapper if M1144 exact recheck fails
- do not treat diagnostic pass as promotion

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1156-v4-public-base-row15-promoted-projection-family-behavior-run
- type: gate
- checkpoint: runs/m1156_row15_promoted_projection_expanded_public_diagnostic/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_promoted_projection_expanded_diagnostic_pass_route_to_result_audit
- reason: M1156 alpha_0_05 keeps M1144 exact delta -0.000378 and passes exact proof old-public replay family-intersection source-diverse fresh/OOD and behavior diagnostics with no training PPO promotion private holdout or actor-input change

## Next Blocker

m1157-v4-public-base-row15-promoted-projection-diagnostic-result-audit
