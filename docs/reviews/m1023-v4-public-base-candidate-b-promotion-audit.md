# m1023-v4-public-base-candidate-b-promotion-audit Research Review

## Summary

- Generated at UTC: 20260526T203504Z
- Type: gate
- Gate tier: promotion
- Promotion decision: candidate_b_promote_public_gate_base
- Decision reason: M1023 promotes Candidate B as the current public-gate base after M1019 full public replay and M1022 promotion/generalization gates pass; no PPO private holdout or paper-level claim

## Hypothesis

Candidate B should replace M974 as the current public-gate base if M1019 and M1022 evidence is complete and promotion remains scoped to public-gate status.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt, runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- parent_dataset: runs/m1019_v4_public_base_m1013_candidate_b_full_replay_gate/summary.json, runs/m1022_v4_public_base_candidate_b_promotion_generalization_gate/summary.json, docs/m1022-v4-public-base-candidate-b-promotion-generalization-gate.md
- parent_config: experiments/manifests/m1022-v4-public-base-candidate-b-promotion-generalization-gate.json
- parent_objective: audit whether Candidate B should replace M974 as the current public-gate base
- derived_from: m1022-v4-public-base-candidate-b-promotion-generalization-gate
- blocked_by: Candidate B passed promotion/generalization gates but has not been explicitly promoted or rejected
- supersedes: None
- invalidates: using Candidate B as the public base before explicit promotion audit

## Success Criteria

- promotion audit artifact exists
- M1019 and M1022 evidence are summarized
- promotion decision is explicit
- current-status and scoreboard lineage are updated if promoted
- PPO, private holdout, and paper-level claims remain blocked

## Failure Criteria

- promotion decision is missing
- promotion occurs without current-status update
- private holdout is used
- PPO starts
- paper-level generalization is claimed

## Evidence Gates

- M1023 must audit M1019 and M1022 evidence
- M1023 must decide promote or reject for public-gate base status
- M1023 must not train or run PPO
- M1023 must not use private holdout
- M1023 must preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not change actor inputs
- do not use private holdout
- do not promote without updating current status and scoreboard lineage
- do not claim paper-level generalization

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1023-v4-public-base-candidate-b-promotion-audit
- type: driver_candidate
- checkpoint: runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: candidate_b_promote_public_gate_base
- reason: M1023 promotes Candidate B as the current public-gate base after M1019 full public replay and M1022 promotion/generalization gates pass; no PPO private holdout or paper-level claim

## Next Blocker

m1024-v4-public-base-candidate-b-post-promotion-synthesis
