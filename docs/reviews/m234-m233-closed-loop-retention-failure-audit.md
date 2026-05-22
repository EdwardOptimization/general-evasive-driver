# m234-m233-closed-loop-retention-failure-audit Research Review

## Summary

- Generated at UTC: 20260522T132655Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_closed_loop_trajectory_anchor_surface
- Decision reason: M234 classifies M233 as closed-loop rollout drift: first-action differences are tiny but M183 row16 flips by margin -0.000275 and protected key leaves the 0.2 window; export trajectory anchors before more PPO

## Hypothesis

M233 fails because snippet-level first-action anchoring can be satisfied while closed-loop near-boundary rollout margins still drift. The next repair should be designed around rollout-level retention rather than another coverage-only snippet export.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m233_protected_key_combined_anchor_from_m224_seed5220/checkpoint.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m233_m183_m170_replay_gate_seed9510/boundary_replay_rows.csv, runs/m233_critical_key_seed9944/guard_results.csv
- parent_config: configs/ppo_m233_protected_key_combined_anchor_from_m224_smoke.json
- parent_objective: combined M223/M231 preferred-only snippet action anchor, combined M223/M231 outcome intervention auxiliary loss, rollout-state M224 baseline action anchor
- derived_from: m233-protected-key-aware-ppo-smoke-from-m224
- blocked_by: m233-protected-key-aware-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- classify whether M233 failure is first-action mismatch or closed-loop rollout drift
- identify the exact failed replay row and protected-key margin movement
- decide the next repair path before any more PPO
- keep M224 current best
- pre-register exactly one bounded next milestone

## Failure Criteria

- run more PPO before the audit
- promote M233 because behavior success is retained
- ignore the M183 M170 replay failure
- ignore the protected-key failure
- change the actor input contract

## Evidence Gates

- M233 M183 M170 replay failed row audit
- M233 protected key candidate audit
- M233 train snippet anchor loss audit
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not repeat or lengthen M233 before the audit
- do not loosen replay or protected-key thresholds
- do not treat near-zero first-action anchor loss as closed-loop retention
- do not change actor inputs

## Failure Taxonomy

- proof_washout
- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m234-m233-closed-loop-retention-failure-audit
- type: gate
- checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844231
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: repair_with_closed_loop_trajectory_anchor_surface
- reason: M234 classifies M233 as closed-loop rollout drift: first-action differences are tiny but M183 row16 flips by margin -0.000275 and protected key leaves the 0.2 window; export trajectory anchors before more PPO

## Next Blocker

Export a closed-loop trajectory anchor surface before any further PPO continuation.
