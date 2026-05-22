# m246-source-balanced-outcome-loss-design Research Review

## Summary

- Generated at UTC: 20260522T142622Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_source_balanced_outcome_loss_implementation
- Decision reason: M246 selects source-balanced outcome intervention losses with protected-key source non-regression as a lexicographic gate before any new PPO; keep M239 as public-gate base

## Hypothesis

M243 regressed the protected-key source because the PPO auxiliary objective and gate treated the combined M232 corpus as one surface. A bounded repair should separate protected-key non-regression from broad M223 improvement before any new PPO.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m245_source_aware_exact_m232_eval/source_summary.csv
- parent_config: configs/ppo_m243_exact_gated_from_m239_smoke.json
- parent_objective: source-aware exact objective gate, outcome intervention auxiliary loss, protected-key non-regression
- derived_from: m245-source-aware-exact-objective-evaluator
- blocked_by: m245-source-aware-exact-objective-evaluator
- supersedes: None
- invalidates: None

## Success Criteria

- identify why the current M243 training objective can improve M223 while regressing protected-key source
- choose one bounded training repair that can be implemented and tested
- pre-register lexicographic exact gate criteria for the next PPO candidate
- keep M239 alpha 0.5 as current public-gate base

## Failure Criteria

- run PPO before choosing a bounded repair
- use M223-only improvement as a continuation criterion
- ignore protected-key source deltas
- change the actor input contract

## Evidence Gates

- M245 source-aware exact reports
- M243 config/objective audit
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M246
- do not change actor inputs
- do not loosen the protected-key guard
- do not proceed with another M243-style combined-only outcome loss

## Failure Taxonomy

- none

## Scoreboard

- milestone: m246-source-balanced-outcome-loss-design
- type: gate
- checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_source_balanced_outcome_loss_implementation
- reason: M246 selects source-balanced outcome intervention losses with protected-key source non-regression as a lexicographic gate before any new PPO; keep M239 as public-gate base

## Next Blocker

Implement source-balanced outcome losses before PPO.
