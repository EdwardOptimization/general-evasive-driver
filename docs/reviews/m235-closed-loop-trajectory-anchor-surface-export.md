# m235-closed-loop-trajectory-anchor-surface-export Research Review

## Summary

- Generated at UTC: 20260522T133202Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_trajectory_action_anchor_implementation
- Decision reason: M235 exports 97 finite M224 trajectory anchor rows for failed M183 row16 and protected key 9944 with protected margin matching M224 guard; no PPO and no driver promotion

## Hypothesis

M233 showed that first-action snippet anchoring is insufficient for near-boundary closed-loop proof retention. Exporting teacher-forced M224 action trajectories for fragile replay and protected rows will create the right surface for a future trajectory-level anchor.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m233_m183_m170_replay_gate_seed9510/boundary_replay_rows.csv, runs/m233_critical_key_seed9944/protected_cases.csv, runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz
- parent_config: configs/ppo_m233_protected_key_combined_anchor_from_m224_smoke.json
- parent_objective: closed-loop replay retention, multi-step action trajectory anchoring
- derived_from: m234-m233-closed-loop-retention-failure-audit
- blocked_by: m233-protected-key-aware-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- export a multi-step trajectory anchor NPZ with deployable observations hidden states reference actions row ids and step indices
- include failed M183 M170 row 16
- include protected key 9944|perturbed|28|28
- validate all arrays are finite and shape-consistent
- do not run PPO or promote a driver checkpoint

## Failure Criteria

- run PPO before trajectory export validation
- export only the same first-action snippets as M232
- omit the failed M183 M170 row
- omit the protected key
- change the human-view actor input contract

## Evidence Gates

- trajectory corpus shape validation
- failed M183 M170 row 16 inclusion
- protected key 9944 inclusion
- M224 reference action reconstruction
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M235
- do not change actor inputs
- do not loosen replay or protected-key thresholds
- do not export only first-action snippets

## Failure Taxonomy

- none

## Scoreboard

- milestone: m235-closed-loop-trajectory-anchor-surface-export
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_trajectory_action_anchor_implementation
- reason: M235 exports 97 finite M224 trajectory anchor rows for failed M183 row16 and protected key 9944 with protected margin matching M224 guard; no PPO and no driver promotion

## Next Blocker

Implement a trajectory-level action anchor loader and PPO loss before any further PPO continuation.
