# m416-active-set-hinge-anchor-implementation Research Review

## Summary

- Generated at UTC: 20260523T164436Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m417_active_set_hinge_projection_probe
- Decision reason: M416 implements optional radius-aware trajectory hinge loss and exports a 192-row active-set hinge anchor that loads in no-update exact repair with exact no-regression

## Hypothesis

A radius-aware trajectory hinge residual can represent active-set replay constraints without globally penalizing harmless recovery movement.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m414_source_weighted_m267_m264_first_replay/boundary_replay_rows.csv, runs/m414_source_weighted_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m409_m407_m267_replay_failure_trajectory_anchor/rejected_trajectory_anchor.npz, runs/m410_old_key_replay_failure_trajectory_anchor/old_key_replay_failure_trajectory_anchor.npz
- parent_config: experiments/manifests/m415-active-set-replay-hinge-design.json
- parent_objective: implement optional radius-aware trajectory hinge residual and active-set anchor export
- derived_from: m415-active-set-replay-hinge-design
- blocked_by: m414-source-weighted-replay-anchor-probe
- supersedes: None
- invalidates: None

## Success Criteria

- trajectory anchor loader supports optional radius with backward compatibility
- hinge loss is zero inside radius and positive outside radius
- active-set hinge anchor artifact includes M267 rows 6 and 15 plus old-key cases 10004, 9998, and 10023
- no-update exact repair smoke loads the hinge anchor with finite loss
- focused tests and research validation pass

## Failure Criteria

- radius schema breaks existing trajectory anchors
- hinge loss cannot be loaded by exact_post_ppo_repair
- actor input or output contract changes
- research validation fails

## Evidence Gates

- infrastructure smoke only
- no PPO run
- no checkpoint promotion
- no actor input/output change
- radius-aware trajectory anchor loads in exact_post_ppo_repair no-update smoke

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m416-active-set-hinge-anchor-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m417_active_set_hinge_projection_probe
- reason: M416 implements optional radius-aware trajectory hinge loss and exports a 192-row active-set hinge anchor that loads in no-update exact repair with exact no-regression

## Next Blocker

m417-active-set-hinge-projection-probe
