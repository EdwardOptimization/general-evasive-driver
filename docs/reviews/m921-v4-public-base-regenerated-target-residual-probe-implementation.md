# m921-v4-public-base-regenerated-target-residual-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T215635Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_regenerated_target_probe_no_candidate_route_to_objective_audit
- Decision reason: M921 joins 122 targets and trains residual-only with actor unchanged but candidate_alpha_count is zero because tail lift fails inside normal-retention range

## Hypothesis

A frozen-M399 residual head trained on M919 regenerated targets can produce at least one normal-retaining alpha that improves low-tail sequence objective metrics.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m920-v4-public-base-regenerated-target-residual-objective-design.md, runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
- parent_config: experiments/manifests/m920-v4-public-base-regenerated-target-residual-objective-design.json
- parent_objective: implement frozen-M399 regenerated-target residual-head objective probe
- derived_from: m920-v4-public-base-regenerated-target-residual-objective-design
- blocked_by: M920 design has not yet been implemented
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- residual_head.pt exists
- sample_reconstruction_success_rate >= 0.98
- actor_backbone_changed is false
- candidate_alpha_count >= 1
- training_started is true
- ppo_used and promoted are false

## Failure Criteria

- actor backbone changes
- sample reconstruction fails
- candidate_alpha_count == 0
- M921 runs exact compatibility replay PPO or promotion

## Evidence Gates

- M921 may train only a residual head
- M921 must keep the M399 actor backbone unchanged
- M921 must write target weight, alpha metrics, objective rows, residual head, and summary artifacts
- M921 must block M880 exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update the M399 actor backbone
- do not change actor inputs
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m921-v4-public-base-regenerated-target-residual-probe-implementation
- type: infrastructure
- checkpoint: runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_regenerated_target_probe_no_candidate_route_to_objective_audit
- reason: M921 joins 122 targets and trains residual-only with actor unchanged but candidate_alpha_count is zero because tail lift fails inside normal-retention range

## Next Blocker

regenerated target residual objective has not yet been implemented
