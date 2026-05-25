# m914-v4-public-base-tail-weighted-residual-probe-implementation Research Review

## Summary

- Generated at UTC: 20260525T212852Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_tail_weighted_probe_no_candidate_route_to_branch_synthesis_then_target_regeneration
- Decision reason: M914 reduces low-tail fraction at high alpha but no alpha passes normal-retention plus tail-lift gates so synthesis then target regeneration is next

## Hypothesis

A residual-head-only M399 tail-weighted objective can improve low-tail p10, deficit, and low-tail fraction under normal-retention gates without actor mutation, replay, PPO, or promotion.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m913-v4-public-base-tail-weighted-objective-design.md, runs/m755_v4_sequence_outcome_corpus_export/summary.json, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
- parent_config: experiments/manifests/m913-v4-public-base-tail-weighted-objective-design.json
- parent_objective: implement residual-head-only tail-weighted M399 objective over M912 low-tail rows
- derived_from: m913-v4-public-base-tail-weighted-objective-design
- blocked_by: tail-weighted public-base residual objective has not yet been tested
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- actor_backbone_changed is false
- residual_only_training is true
- residual feature_dim is 128
- sample_reconstruction_success_rate >= 0.98
- metadata_missing_rows is 0
- candidate_alpha_count >= 1
- ppo_used and promoted are false

## Failure Criteria

- actor checksum changes
- reconstruction rate below 0.98
- candidate_alpha_count is 0
- M914 runs M880 exact compatibility, replay, PPO, or promotion

## Evidence Gates

- M914 must train residual head only
- M914 must keep M399 actor checksum unchanged
- M914 must reconstruct at least 98 percent of rows
- M914 must export p10, deficit, and low-tail fraction alpha metrics
- M914 must keep M880 exact compatibility, replay, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not admit a candidate without normal-retention and tail-lift gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m914-v4-public-base-tail-weighted-residual-probe-implementation
- type: infrastructure
- checkpoint: runs/m914_v4_public_base_tail_weighted_residual_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_tail_weighted_probe_no_candidate_route_to_branch_synthesis_then_target_regeneration
- reason: M914 reduces low-tail fraction at high alpha but no alpha passes normal-retention plus tail-lift gates so synthesis then target regeneration is next

## Next Blocker

Tail-weighted M399 residual probe has not yet been run
