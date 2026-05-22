# m229-snippet-anchored-ppo-smoke-from-m224 Research Review

## Summary

- Generated at UTC: 20260522T130115Z
- Type: driver_candidate
- Gate tier: proof
- Promotion decision: reject_protected_key_window_failure
- Decision reason: M229 improves fixed M223 loss to 0.209728 and restores all old/current/new replay gates including M183 M170 17/17 but protected key fails with normal margin 0.205200 above 0.2; keep M224

## Hypothesis

Adding preferred-only boundary snippet action anchoring to the M226 PPO recipe may preserve the proof rows that M226 lost while retaining broad behavior from M224.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
- parent_config: configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- parent_objective: M223 outcome intervention corpus, rollout-state M224 baseline action anchor, preferred-only M224 boundary snippet action anchor
- derived_from: m228-ppo-snippet-action-anchor-implementation
- blocked_by: m226-guarded-ppo-smoke-from-m224
- supersedes: m226-guarded-ppo-smoke-from-m224
- invalidates: None

## Success Criteria

- start from the M224 checkpoint
- run exactly one tiny PPO smoke with configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- keep actor inputs unchanged
- log snippet_action_anchor_loss_mean during training
- preserve M183 M168 and M183 M170 replay gates
- preserve M193 M189, M212 M204, and M223 M219 replay gates
- preserve behavior seeds 9505 and 9506
- preserve protected key 9944|perturbed|28|28
- do not promote unless fixed M223 objective is not worse than M224 within tolerance and every proof surface passes

## Failure Criteria

- snippet_action_anchor_loss_mean is missing
- drop any old/current/new replay row
- protected key leaves the near-boundary window
- behavior success regresses below M224
- fixed M223 objective regresses beyond tolerance
- change actor observation inputs

## Evidence Gates

- fixed M223 outcome objective versus M219/M224/M225/M226
- M183 M168 and M183 M170 old replay surfaces
- M193 M189 refreshed replay surface
- M212 M204 current replay surface
- M223 M219 new replay surface
- behavior seeds 9505 and 9506
- critical protected key seed 9944

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run multiple PPO seeds before this smoke is gated
- do not run longer PPO directly
- do not promote based on training reward
- do not change actor inputs
- do not loosen replay or protected-key thresholds after seeing the result

## Failure Taxonomy

- protected_key_window_failure
- promotion_gate_failure

## Scoreboard

- milestone: m229-snippet-anchored-ppo-smoke-from-m224
- type: driver_candidate
- checkpoint: runs/ppo_m229_snippet_anchor_from_m224_seed5219/checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844862
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: reject_protected_key_window_failure
- reason: M229 improves fixed M223 loss to 0.209728 and restores all old/current/new replay gates including M183 M170 17/17 but protected key fails with normal margin 0.205200 above 0.2; keep M224

## Next Blocker

Audit why M229 restores replay gates but still moves the protected key outside the near-boundary normal-margin window.
