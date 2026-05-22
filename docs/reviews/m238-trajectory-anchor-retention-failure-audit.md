# m238-trajectory-anchor-retention-failure-audit Research Review

## Summary

- Generated at UTC: 20260522T134819Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_checkpoint_interpolation_retention_probe
- Decision reason: M238 finds M237 anchor coverage and teacher-forced action matching are present but on-policy near-boundary margins still drift; classify as trust-region sized closed-loop distribution drift and run no-PPO interpolation probe

## Hypothesis

M237 fails because teacher-forced trajectory action anchoring can be satisfied while the on-policy closed-loop trajectory still drifts on near-boundary proof rows. The audit should identify whether the next repair needs stronger anchoring, hidden/state anchoring, KL tightening, or a different PPO update structure.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m237_trajectory_anchor_from_m224_seed5221/checkpoint.pt
- parent_dataset: runs/m235_closed_loop_trajectory_anchor_surface/trajectory_anchor.npz, runs/m237_m183_m170_replay_gate_seed9510/boundary_replay_rows.csv, runs/m237_critical_key_seed9944/guard_results.csv
- parent_config: configs/ppo_m237_trajectory_anchor_from_m224_smoke.json
- parent_objective: M232 preferred-only snippet action anchor, M235 trajectory action anchor, rollout-state M224 baseline action anchor, outcome intervention auxiliary loss
- derived_from: m237-trajectory-anchored-ppo-smoke-from-m224
- blocked_by: m237-trajectory-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- classify whether M237 failure is anchor strength, anchor coverage, on-policy distribution drift, or PPO trust-region weakness
- quantify the failed M183 M170 row and protected-key margin movement relative to M224 and M233
- decide one bounded next milestone before any more PPO
- keep M224 current best
- pre-register the next repair path

## Failure Criteria

- run more PPO before the audit
- promote M237 because behavior success is retained
- ignore the M183 M170 replay failure
- ignore the protected-key failure
- change the actor input contract

## Evidence Gates

- M237 train trajectory-anchor loss audit
- M237 M183 M170 failed row audit
- M237 protected key candidate audit
- M235 trajectory anchor coverage audit
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not repeat or lengthen M237 before the audit
- do not loosen replay or protected-key thresholds
- do not change actor inputs
- do not treat near-zero teacher-forced trajectory loss as on-policy closed-loop retention

## Failure Taxonomy

- proof_washout
- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m238-trajectory-anchor-retention-failure-audit
- type: gate
- checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844231
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: admit_checkpoint_interpolation_retention_probe
- reason: M238 finds M237 anchor coverage and teacher-forced action matching are present but on-policy near-boundary margins still drift; classify as trust-region sized closed-loop distribution drift and run no-PPO interpolation probe

## Next Blocker

Run a bounded no-PPO interpolation sweep from M224 toward M237 to separate trust-region magnitude from objective design failure.
