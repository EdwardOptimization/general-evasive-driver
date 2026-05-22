# m228-ppo-snippet-action-anchor-implementation Research Review

## Summary

- Generated at UTC: 20260522T125433Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m229_snippet_anchored_ppo_smoke
- Decision reason: M228 adds train_ppo snippet_action_anchor_coef/checkpoint/snapshot/batch/preferred_only config plus snippet_action_anchor_loss_mean logging and focused tests; no driver checkpoint promoted

## Hypothesis

PPO needs the same boundary snippet-level action anchor that stabilized M224/M225 actor updates; adding this loss path to train_ppo should make a later M229 PPO smoke testable without changing actor inputs or loosening gates.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
- parent_config: configs/ppo_m226_guarded_from_m224_smoke.json
- parent_objective: M223 outcome intervention corpus, M224 preferred-only snippet action anchor
- derived_from: m227-ppo-smoke-retention-failure-audit
- blocked_by: m226-guarded-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- train_ppo config supports a snippet-level action anchor checkpoint, snippet corpus, coefficient, batch size, and preferred-only mode
- the snippet action anchor uses boundary outcome snippets rather than rollout-only states
- the implementation is covered by focused unit tests
- no PPO or driver promotion is claimed in this infrastructure milestone
- M229 PPO smoke is pre-registered only after implementation tests pass

## Failure Criteria

- run PPO before the snippet anchor implementation is tested
- reuse only rollout-state action anchoring
- anchor rejected hidden states by default when the protected recipe requires preferred-only
- change the human-view actor input contract
- loosen M183/M223/protected-key gates

## Evidence Gates

- unit tests for PPO config validation
- unit tests for snippet action anchor loss on outcome snippets
- research validator
- pre-commit lightweight harness

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M228
- do not change actor inputs
- do not loosen replay/protected-key thresholds
- do not reuse private holdouts for repair

## Failure Taxonomy

- none

## Scoreboard

- milestone: m228-ppo-snippet-action-anchor-implementation
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m229_snippet_anchored_ppo_smoke
- reason: M228 adds train_ppo snippet_action_anchor_coef/checkpoint/snapshot/batch/preferred_only config plus snippet_action_anchor_loss_mean logging and focused tests; no driver checkpoint promoted

## Next Blocker

Run one M229 PPO smoke from M224 using rollout action anchor plus preferred-only snippet action anchor, then gate old/current/new replay, behavior, and protected key.
