# m244-m243-protected-key-objective-conflict-audit Research Review

## Summary

- Generated at UTC: 20260522T141656Z
- Type: gate
- Gate tier: process
- Promotion decision: repair_with_source_aware_lexicographic_exact_gate
- Decision reason: M244 reproduces exact M232 and decomposes M243 movement: M223 rows improve but protected-key row regresses enough to dominate combined M232; keep M239 and implement source-aware exact evaluator

## Hypothesis

M243 improves the old M223 rows while regressing the combined M232 objective because the protected-key component moves in the wrong direction. A per-row exact audit should identify whether the next repair needs protected-key reweighting, a separate protected-key loss, or a stricter lexicographic objective gate.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m243_exact_gated_from_m239_seed5223/checkpoint.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz
- parent_config: configs/ppo_m243_exact_gated_from_m239_smoke.json
- parent_objective: exact M232 objective, exact M223 objective, protected-key objective component
- derived_from: m243-exact-gated-ppo-smoke-from-m239
- blocked_by: m243-exact-gated-ppo-smoke-from-m239
- supersedes: None
- invalidates: None

## Success Criteria

- compute per-row exact objective deltas for M239 to M243
- separate M223-row movement from protected-key movement
- decide one bounded next repair before any more PPO
- keep M239 alpha 0.5 as current public-gate base

## Failure Criteria

- run PPO before the audit
- promote M243 despite M232 regression
- collapse M223 and protected-key objective movement into one aggregate
- change the actor input contract

## Evidence Gates

- M243 per-row exact M232 objective audit
- M223 versus protected-key component comparison
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run more PPO before the audit
- do not promote M243 because M223 improves
- do not ignore protected-key row movement
- do not change actor inputs

## Failure Taxonomy

- objective_overfit
- promotion_gate_failure

## Scoreboard

- milestone: m244-m243-protected-key-objective-conflict-audit
- type: gate
- checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: repair_with_source_aware_lexicographic_exact_gate
- reason: M244 reproduces exact M232 and decomposes M243 movement: M223 rows improve but protected-key row regresses enough to dominate combined M232; keep M239 and implement source-aware exact evaluator

## Next Blocker

Implement source-aware exact objective reporting so future PPO gates can require protected-key non-regression separately from M223 improvement.
