# m1127-v4-public-base-row15-projection-full-public-gate Research Review

## Summary

- Generated at UTC: 20260527T215734Z
- Type: gate
- Gate tier: promotion
- Promotion decision: row15_projection_full_public_gate_pass_route_to_branch_synthesis
- Decision reason: M1127 alpha_0_15 passes M1107 exact recheck and the expanded full public gate: exact proof family-intersection source-diverse generalization and behavior tiers all pass with no actor-input change PPO promotion or private holdout

## Hypothesis

Alpha_0_15 passes M1107 exact recheck and the expanded full public gate after passing row15 unsafe-margin and family-intersection replay.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1126-v4-public-base-row15-projection-full-public-gate-design.md, runs/m1123_row15_unsafe_margin_projection_probe/summary.json, runs/m1125_row15_projection_family_replay/summary.json
- parent_config: experiments/manifests/m1126-v4-public-base-row15-projection-full-public-gate-design.json
- parent_objective: run M1107 exact recheck and expanded full public gate for alpha_0_15
- derived_from: m1126-v4-public-base-row15-projection-full-public-gate-design
- blocked_by: alpha_0_15 has not yet passed expanded full public gate
- supersedes: None
- invalidates: promotion before full public gate result, PPO from alpha_0_15 before full public gate result, private holdout before public gate result

## Success Criteria

- M1107 exact recheck summary exists and passes
- expanded full public gate summary exists
- result_class == candidate_b_combined_active_set_full_public_gate_candidate
- exact_pass proof_pass family_intersection_pass source_diverse_pass generalization_pass behavior_pass are all true
- actor_inputs_changed == false
- no actor training, PPO, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- M1107 exact recheck fails
- expanded full public gate summary is missing
- any full public gate tier fails
- actor_inputs_changed == true
- actor training, PPO, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1127 must run M1107 exact recheck first
- M1127 may run the expanded full public gate for alpha_0_15
- M1127 must not train actor weights
- M1127 must not run PPO
- M1127 must not promote
- M1127 must not use private holdout
- M1127 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not promote
- do not use private holdout
- do not change actor inputs
- do not skip M1107 exact recheck
- do not skip any expanded full public gate tier
- do not switch candidates after seeing gate failure

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1127-v4-public-base-row15-projection-full-public-gate
- type: gate
- checkpoint: runs/m1127_row15_projection_full_public_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_full_public_gate_pass_route_to_branch_synthesis
- reason: M1127 alpha_0_15 passes M1107 exact recheck and the expanded full public gate: exact proof family-intersection source-diverse generalization and behavior tiers all pass with no actor-input change PPO promotion or private holdout

## Next Blocker

m1128-v4-public-base-row15-projection-branch-synthesis
