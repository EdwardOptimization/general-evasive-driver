# m237-trajectory-anchored-ppo-smoke-from-m224 Research Review

## Summary

- Generated at UTC: 20260522T134426Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_trajectory_anchor_ppo_smoke
- Decision reason: M237 improves fixed losses and keeps behavior stable but M183 M170 replay stays 16/17 and protected key fails at normal margin 0.204386 despite near-zero trajectory anchor loss; keep M224 and audit retention

## Hypothesis

Trajectory-level action anchoring should preserve the failed M183 M170 row and protected key better than M233's first-action snippet-only repair.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz
- parent_config: configs/ppo_m233_protected_key_combined_anchor_from_m224_smoke.json
- parent_objective: combined M223/M231 snippet action anchor, M235 trajectory action anchor, rollout-state M224 baseline action anchor
- derived_from: m236-trajectory-action-anchor-implementation
- blocked_by: m233-protected-key-aware-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- run exactly one 1024-step PPO smoke from M224 with M232 snippet anchor and M235 trajectory anchor
- retain M183 M170 replay at 17/17 success drops
- pass protected key 9944 within the existing normal-margin window
- retain behavior seed success at the M224 level
- do not repeat or lengthen PPO before the one-smoke result is audited

## Failure Criteria

- M183 M170 replay drops below 17/17
- protected key 9944 fails
- behavior seed success regresses materially
- trajectory_action_anchor_loss_mean is missing from training metrics
- actor input contract changes

## Evidence Gates

- fixed M223/M232 objective evaluation
- M183 replay gates
- M193 replay gate
- M212 replay gate
- M223 replay gate
- behavior seeds 9505 and 9506
- protected key 9944 guard
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change actor inputs
- do not loosen replay or protected-key thresholds
- do not lengthen PPO before this one-smoke gate passes
- do not promote if M183 M170 or protected key fails

## Failure Taxonomy

- proof_washout
- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m237-trajectory-anchored-ppo-smoke-from-m224
- type: driver_candidate
- checkpoint: runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844021
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: reject_trajectory_anchor_ppo_smoke
- reason: M237 improves fixed losses and keeps behavior stable but M183 M170 replay stays 16/17 and protected key fails at normal margin 0.204386 despite near-zero trajectory anchor loss; keep M224 and audit retention

## Next Blocker

Audit why trajectory anchoring still fails on-policy closed-loop proof retention before any more PPO.
