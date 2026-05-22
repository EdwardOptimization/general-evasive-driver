# m232-protected-key-combined-snippet-anchor-corpus Research Review

## Summary

- Generated at UTC: 20260522T131709Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_protected_key_aware_ppo_smoke
- Decision reason: M232 combines all 17 M223 rows plus protected key 9944 into one validated 18-row anchor corpus with positive weights and loader validation; no PPO and no driver promotion

## Hypothesis

A later protected-key-aware PPO repair should anchor both the M223 replay proof surface and the M231 protected key. Building one validated combined corpus first avoids protecting the historical key while accidentally dropping the broader replay surface.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.csv
- parent_config: configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- parent_objective: preferred-only M224 boundary snippet action anchoring, protected-key normal-margin-window retention
- derived_from: m231-protected-key-snippet-surface-export
- blocked_by: m229-snippet-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- export a combined snippet-action-anchor NPZ compatible with PPO snippet_action_anchor_snapshot_npz
- include all 17 M223 rows plus the protected key 9944 row
- validate observation hidden action and weight shapes
- validate all weights are finite and positive
- do not run PPO or promote a driver checkpoint

## Failure Criteria

- run PPO before the combined corpus is validated
- drop any M223 proof-surface rows
- omit the 9944 protected key
- produce zero or non-finite weights
- change the human-view actor input contract

## Evidence Gates

- combined corpus shape validation
- M223 row-count retention
- protected key 9944 inclusion
- PPO snippet-action-anchor loader validation
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M232
- do not change actor inputs
- do not drop any M223 snippet rows
- do not loosen the protected-key normal-margin window

## Failure Taxonomy

- none

## Scoreboard

- milestone: m232-protected-key-combined-snippet-anchor-corpus
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_protected_key_aware_ppo_smoke
- reason: M232 combines all 17 M223 rows plus protected key 9944 into one validated 18-row anchor corpus with positive weights and loader validation; no PPO and no driver promotion

## Next Blocker

Run one bounded M233 protected-key-aware PPO smoke from M224 using rollout action anchor plus the combined M223/M231 snippet action anchor.
