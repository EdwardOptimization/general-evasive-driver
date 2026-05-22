# m236-trajectory-action-anchor-implementation Research Review

## Summary

- Generated at UTC: 20260522T133634Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_trajectory_anchored_ppo_smoke
- Decision reason: M236 adds trajectory anchor loader loss config logging and focused tests with 58 passed; no PPO and no driver promotion

## Hypothesis

A trajectory-level action anchor can protect multi-step closed-loop proof surfaces better than first-action snippet anchors. M236 should implement the loader/loss path and tests before any new PPO smoke.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.csv
- parent_config: configs/ppo_m233_protected_key_combined_anchor_from_m224_smoke.json
- parent_objective: multi-step trajectory action anchoring, closed-loop proof retention
- derived_from: m235-closed-loop-trajectory-anchor-surface-export
- blocked_by: m233-protected-key-aware-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- add a trajectory anchor loader that validates observation hidden reference_action source_index step_index and positive weights
- add a trajectory action anchor loss that anchors model action means to reference_action
- wire optional trajectory_action_anchor config fields into train_ppo
- log trajectory_action_anchor_loss_mean when enabled
- cover the new path with focused tests
- do not run PPO or promote a driver checkpoint

## Failure Criteria

- run PPO before implementation tests pass
- depend on hidden privileged actor inputs
- anchor only first-action snippets
- silently accept malformed trajectory arrays
- change the human-view actor input contract

## Evidence Gates

- trajectory anchor loader unit tests
- trajectory anchor loss unit tests
- train_ppo config validation tests
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M236
- do not change actor inputs
- do not loosen replay or protected-key thresholds
- do not replace replay gates with training loss values

## Failure Taxonomy

- none

## Scoreboard

- milestone: m236-trajectory-action-anchor-implementation
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_trajectory_anchored_ppo_smoke
- reason: M236 adds trajectory anchor loader loss config logging and focused tests with 58 passed; no PPO and no driver promotion

## Next Blocker

Run one bounded M237 PPO smoke from M224 with the combined snippet anchor and new trajectory action anchor, then gate replay behavior and protected key.
