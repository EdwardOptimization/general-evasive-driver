# m924-v4-public-base-alpha-aware-low-tail-residual-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T220819Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_alpha_aware_low_tail_probe_no_candidate_route_to_branch_synthesis
- Decision reason: M924 strongly improves low-tail metrics but violates normal retention and worsens target loss at useful alphas so no candidate alpha is admitted

## Hypothesis

Alpha-aware low-tail losses evaluated inside the normal-retention alpha range can produce an admitted residual-head alpha where M921 target-action imitation failed.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m923-v4-public-base-alpha-aware-low-tail-objective-design.md, runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv, runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json, runs/m921_v4_public_base_regenerated_target_residual_probe/alpha_metrics.csv, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv
- parent_config: experiments/manifests/m923-v4-public-base-alpha-aware-low-tail-objective-design.json
- parent_objective: implement alpha-aware low-tail residual objective after M921 no-candidate result
- derived_from: m923-v4-public-base-alpha-aware-low-tail-objective-design
- blocked_by: M923 alpha-aware low-tail objective design
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
- M924 runs exact compatibility replay PPO or promotion

## Evidence Gates

- M924 may train only a residual head
- M924 must optimize low-tail metrics at normal-retaining train alphas
- M924 must keep the M399 actor backbone unchanged
- M924 must block exact compatibility, replay, PPO, and promotion

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

- milestone: m924-v4-public-base-alpha-aware-low-tail-residual-probe-implementation
- type: infrastructure
- checkpoint: runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_alpha_aware_low_tail_probe_no_candidate_route_to_branch_synthesis
- reason: M924 strongly improves low-tail metrics but violates normal retention and worsens target loss at useful alphas so no candidate alpha is admitted

## Next Blocker

alpha-aware low-tail residual objective has not yet been implemented
