# m231-protected-key-snippet-surface-export Research Review

## Summary

- Generated at UTC: 20260522T131402Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_combined_anchor_corpus_build
- Decision reason: M231 exports one validated protected-key snippet for 9944|perturbed|28|28 with shapes 1x72 1x128 1x3 and positive weight 0.051482; no PPO and no driver promotion

## Hypothesis

M229 failed the protected key because the M223 snippet anchor surface does not cover that key. Exporting a protected-key snippet/action-anchor surface will make the missing proof row explicit before any further PPO.

## Lineage

- parent_checkpoint: runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt, runs/ppo_m229_snippet_anchor_from_m224_seed5219/checkpoint.pt
- parent_dataset: runs/m229_critical_key_seed9944/protected_cases.csv, runs/m229_critical_key_seed9944/guard_results.csv, runs/m229_critical_key_seed9944/m224_10063_candidates.csv
- parent_config: configs/ppo_m229_snippet_anchor_from_m224_smoke.json
- parent_objective: protected-key normal-margin-window retention, preferred-only snippet action anchoring
- derived_from: m230-m229-protected-key-failure-audit
- blocked_by: m229-snippet-anchored-ppo-smoke-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- export a protected-key snippet npz compatible with PPO snippet_action_anchor_snapshot_npz
- include deployable observation and recurrent hidden states for the protected key or a small protected-key family
- anchor actions to M224 without adding privileged actor inputs
- validate array shapes and positive weights
- do not run PPO or promote a driver checkpoint

## Failure Criteria

- run PPO before export validation
- depend on hidden privileged parameters as actor inputs
- omit the 9944 protected key
- produce a snippet corpus with zero or non-finite weights

## Evidence Gates

- protected key 9944 export
- shape validation for observation/hidden/action/weight arrays
- M224 reference action reconstruction
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M231
- do not change actor inputs
- do not loosen the protected-key normal-margin window
- do not train lower clearance just to satisfy one key

## Failure Taxonomy

- none

## Scoreboard

- milestone: m231-protected-key-snippet-surface-export
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_combined_anchor_corpus_build
- reason: M231 exports one validated protected-key snippet for 9944|perturbed|28|28 with shapes 1x72 1x128 1x3 and positive weight 0.051482; no PPO and no driver promotion

## Next Blocker

Combine the protected-key surface with M223 snippets before any protected-key-aware PPO repair.
