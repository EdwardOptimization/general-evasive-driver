# m909-v4-public-base-residual-head-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T210425Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_residual_head_probe_no_gap_lift_blocked
- Decision reason: M909 produces a 128-dim residual head and keeps actor unchanged but candidate_alpha_count is zero so the head is not admitted for M880 exact or replay

## Hypothesis

The existing residual-only sequence objective probe can train a finite 128-dim residual head for frozen M399 without actor mutation, replay, PPO, or promotion.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m908-v4-public-base-compatible-residual-head-probe-design.md, runs/m755_v4_sequence_outcome_corpus_export/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m908-v4-public-base-compatible-residual-head-probe-design.json
- parent_objective: train residual head only on frozen M399 recurrent actor features
- derived_from: m908-v4-public-base-compatible-residual-head-probe-design
- blocked_by: public-base-compatible 128-dim residual head does not yet exist
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- actor_backbone_changed is false
- residual_only_training is true
- ppo_used and promoted are false
- sample_reconstruction_success_rate >= 0.98
- metadata_missing_rows is 0
- residual_head_pt exists
- residual feature_dim is 128
- residual_parameter_count is 8451
- candidate_alpha_count >= 1

## Failure Criteria

- actor checksum changes
- residual feature_dim is not 128
- reconstruction rate below 0.98
- candidate_alpha_count is 0
- M909 runs replay, PPO, actor update, or promotion

## Evidence Gates

- M909 must load M399 public base
- M909 must train residual head only
- M909 must keep actor checksum unchanged
- M909 must produce residual_head.pt with feature_dim 128
- M909 must keep replay, PPO, actor update, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not load M761 residual head as the candidate residual
- do not modify actor inputs
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m909-v4-public-base-residual-head-probe-implementation
- type: infrastructure
- checkpoint: runs/m909_v4_public_base_residual_head_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_residual_head_probe_no_gap_lift_blocked
- reason: M909 produces a 128-dim residual head and keeps actor unchanged but candidate_alpha_count is zero so the head is not admitted for M880 exact or replay

## Next Blocker

M399-compatible residual head has not yet been generated
