# m1125-v4-public-base-row15-projection-family-replay Research Review

## Summary

- Generated at UTC: 20260527T214242Z
- Type: gate
- Gate tier: proof
- Promotion decision: row15_projection_family_replay_pass_route_to_full_public_gate_design
- Decision reason: M1125 alpha_0_15 passes M1061 family-intersection public gate with 3 of 3 replay gates passed all success drops retained actor inputs unchanged and no PPO promotion or private holdout

## Hypothesis

Alpha_0_15 preserves the M1061 family-intersection proof rows after passing row15 unsafe-margin and target-base first replay.

## Lineage

- parent_checkpoint: runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
- parent_dataset: docs/m1124-v4-public-base-row15-projection-family-replay-design.md, runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv, runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv, runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.csv
- parent_config: experiments/manifests/m1124-v4-public-base-row15-projection-family-replay-design.json
- parent_objective: run M1061 family-intersection public gate for alpha_0_15
- derived_from: m1124-v4-public-base-row15-projection-family-replay-design
- blocked_by: alpha_0_15 has not yet passed M1061 family-intersection replay
- supersedes: None
- invalidates: full public gate before family-intersection replay, fresh/OOD before family-intersection replay, PPO from alpha_0_15, promotion of alpha_0_15

## Success Criteria

- family_intersection_public_gate summary exists
- result_class == family_intersection_public_gate_pass
- overall_pass == true
- replay_gate_count == 3
- replay_gates_passed == 3
- actor_inputs_changed == false
- no actor training, PPO, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change occurs

## Failure Criteria

- family_intersection_public_gate summary is missing
- any source-to-candidate replay gate fails
- actor_inputs_changed == true
- actor training, PPO, full public gate, fresh/OOD, behavior gate, promotion, private holdout, or actor-input change starts

## Evidence Gates

- M1125 may run only the M1061 family-intersection public gate for alpha_0_15
- M1125 must not train actor weights
- M1125 must not run PPO
- M1125 must not run full public gate
- M1125 must not run fresh/OOD or behavior gates
- M1125 must not promote
- M1125 must not use private holdout
- M1125 must preserve actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train actor weights
- do not run PPO
- do not run full public gate
- do not run fresh/OOD or behavior gates
- do not promote
- do not use private holdout
- do not change actor inputs
- do not weaken family-intersection thresholds

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1125-v4-public-base-row15-projection-family-replay
- type: gate
- checkpoint: runs/m1125_row15_projection_family_replay/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: row15_projection_family_replay_pass_route_to_full_public_gate_design
- reason: M1125 alpha_0_15 passes M1061 family-intersection public gate with 3 of 3 replay gates passed all success drops retained actor inputs unchanged and no PPO promotion or private holdout

## Next Blocker

m1126-v4-public-base-row15-projection-full-public-gate-design
