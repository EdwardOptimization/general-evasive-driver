# m227-ppo-smoke-retention-failure-audit Research Review

## Summary

- Generated at UTC: 20260522T124852Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_ppo_snippet_action_anchor
- Decision reason: M227 classifies M226 as proof_washout and protected_key_window_failure: PPO kept broad behavior but only anchored rollout states while M224/M225 stability came from preferred-only boundary snippet action anchors; keep M224 and implement M228 before any more PPO

## Hypothesis

M226 shows that ordinary guarded PPO with rollout action anchoring and the M223 outcome corpus can still lose proof-surface retention: M183 M170 drops one row and the historical protected key leaves the near-boundary window. Before any more PPO, audit whether PPO needs snippet-level action anchoring or another replay-surface retention mechanism.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m226_guarded_from_m224_seed5218/checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
- parent_config: configs/ppo_m226_guarded_from_m224_smoke.json
- parent_objective: M223 outcome intervention corpus, PPO rollout-state action anchor
- derived_from: m224-m223-guarded-actor-update, m226-guarded-ppo-smoke-from-m224
- blocked_by: m226-guarded-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- do not run another PPO smoke before the audit is documented
- compare M224 and M226 on fixed M223 objective, M183 M170 replay, and protected key
- separate broad behavior retention from proof-surface retention
- identify why M224/M225 actor updates are stable but M226 PPO is not
- pre-register the next code/config milestone before any more PPO
- keep M224 as current best unless a new gated candidate passes all surfaces

## Failure Criteria

- repeat M226 before audit
- run longer PPO from M226
- promote M226 based on broad behavior
- change actor inputs
- loosen replay or protected-key thresholds after seeing the result

## Evidence Gates

- fixed M223 outcome objective
- M183 M170 old replay surface
- M223 current-family replay surface
- M226 broad behavior seeds 9505 and 9506
- critical protected key seed 9944

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote M226 based on broad behavior alone
- do not loosen replay or protected-key thresholds after seeing failures
- do not run another PPO continuation before a retention audit
- do not change actor inputs while auditing PPO retention

## Failure Taxonomy

- proof_washout
- protected_key_window_failure

## Scoreboard

- milestone: m227-ppo-smoke-retention-failure-audit
- type: gate
- checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844231
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: repair_with_ppo_snippet_action_anchor
- reason: M227 classifies M226 as proof_washout and protected_key_window_failure: PPO kept broad behavior but only anchored rollout states while M224/M225 stability came from preferred-only boundary snippet action anchors; keep M224 and implement M228 before any more PPO

## Next Blocker

Implement PPO snippet-level action anchoring before any more PPO smoke.
