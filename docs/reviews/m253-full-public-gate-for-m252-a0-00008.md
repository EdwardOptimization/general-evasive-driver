# m253-full-public-gate-for-m252-a0-00008 Research Review

## Summary

- Generated at UTC: 20260522T150451Z
- Type: driver_candidate
- Gate tier: promotion
- Promotion decision: promote_m252_a0_00008_public_gate_base
- Decision reason: M253 alpha 0.00008 passes all replay protected-key and behavior gates versus M250 while retaining the stronger exact source improvement from M252

## Hypothesis

The M252 alpha 0.00008 checkpoint is the largest safe source-calibrated alpha and can retain the full public proof, protected-key, and behavior gate stack.

## Lineage

- parent_checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt, runs/m250_nano_custom_m239_to_protected_source_interpolation/checkpoints/alpha_0_00005.pt
- parent_dataset: runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv, runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv, runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv, runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv
- parent_config: configs/m121_human_view_zero_obstacle_relvel.json, docs/m252-nano-alpha-safety-boundary-audit.md
- parent_objective: full public-gate promotion check for largest M252 safe alpha
- derived_from: m252-nano-alpha-safety-boundary-audit
- blocked_by: m252-nano-alpha-safety-boundary-audit
- supersedes: None
- invalidates: None

## Success Criteria

- candidate passes M183 M168, M183 M170, M193 M189, M212 M204, and M223 M219 replay gates
- candidate passes protected key 9944 guard
- candidate retains behavior on seeds 9505 and 9506
- no PPO is run
- no actor-input contract changes

## Failure Criteria

- any replay gate fails
- protected key fails
- behavior seeds materially regress
- PPO is run

## Evidence Gates

- M183 M168 replay gate
- M183 M170 replay gate
- M193 M189 replay gate
- M212 M204 replay gate
- M223 M219 replay gate
- protected key 9944 guard
- behavior seeds 9505 and 9506
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M253
- do not promote on M183 M170 alone
- do not loosen protected-key or behavior gates
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m253-full-public-gate-for-m252-a0-00008
- type: driver_candidate
- checkpoint: runs/m252_alpha_boundary_interpolation/checkpoints/alpha_0_00008.pt
- success_rate: 0.8625
- termination_rate: 0.1375
- clearance_margin_mean: 1.844111
- reset_success: 0.8500
- zero_wheel_success: None
- zero_all_success: 0.8000
- wheel_gain_mu: None
- decision: promote_m252_a0_00008_public_gate_base
- reason: M253 alpha 0.00008 passes all replay protected-key and behavior gates versus M250 while retaining the stronger exact source improvement from M252

## Next Blocker

Run one exact-source-gated PPO smoke from the promoted calibrated base.
