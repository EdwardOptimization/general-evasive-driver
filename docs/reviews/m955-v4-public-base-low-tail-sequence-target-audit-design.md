# m955-v4-public-base-low-tail-sequence-target-audit-design Research Review

## Summary

- Generated at UTC: 20260526T010421Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: low_tail_sequence_target_audit_design_admit_m956
- Decision reason: M955 designs no-training short-horizon sequence target audit with first-action retention sequence low-tail metrics M267 sequence proof retention and threshold-audit fallback

## Hypothesis

M954's zero joint candidates may be a first-action target under-specification, so the next no-training step should design a short-horizon low-tail sequence target audit before changing actor parameters or thresholds.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m954-v4-public-base-replay-constrained-target-feasibility-implementation.md, runs/m954_v4_public_base_replay_constrained_target_feasibility/summary.json, runs/m954_v4_public_base_replay_constrained_target_feasibility/target_family_summary.csv, runs/m954_v4_public_base_replay_constrained_target_feasibility/offline_exact_target_metrics.csv
- parent_config: experiments/manifests/m954-v4-public-base-replay-constrained-target-feasibility-implementation.json
- parent_objective: design a no-training sequence-target audit after one-step target families fail the exact low-tail gate
- derived_from: m954-v4-public-base-replay-constrained-target-feasibility-implementation
- blocked_by: M954 found M267 target preflight is mostly solved but one-step target families have zero exact target candidates
- supersedes: None
- invalidates: more one-step target projection sweeps before sequence or threshold audit

## Success Criteria

- design document exists
- sequence target feasibility metrics are explicit
- normal-retention and low-tail gates remain separated
- M267 proof-retention handling remains explicit
- threshold-audit fallback is specified
- training, PPO, and promotion remain blocked

## Failure Criteria

- design recommends actor training before sequence feasibility
- design changes actor inputs
- design omits M267 proof-retention handling
- design relaxes exact thresholds without a registered sensitivity audit

## Evidence Gates

- M955 must not train
- M955 must not run PPO
- M955 must not promote
- M955 must preserve the P0 actor-input contract
- M955 must design a short-horizon sequence target audit or a threshold audit fallback

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune actor parameters
- do not widen actor inputs
- do not open encoders or GRU
- do not use private holdout
- do not promote
- do not repeat one-step projection sweeps without a new audit variable

## Failure Taxonomy

- none

## Scoreboard

- milestone: m955-v4-public-base-low-tail-sequence-target-audit-design
- type: infrastructure
- checkpoint: docs/m955-v4-public-base-low-tail-sequence-target-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_tail_sequence_target_audit_design_admit_m956
- reason: M955 designs no-training short-horizon sequence target audit with first-action retention sequence low-tail metrics M267 sequence proof retention and threshold-audit fallback

## Next Blocker

m956-v4-public-base-low-tail-sequence-target-audit-implementation
