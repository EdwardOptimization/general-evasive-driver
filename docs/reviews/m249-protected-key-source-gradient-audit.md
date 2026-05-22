# m249-protected-key-source-gradient-audit Research Review

## Summary

- Generated at UTC: 20260522T144048Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_protected_key_source_actor_coupling_calibration
- Decision reason: M249 shows protected-key source loss is strongly steerable in actor-coupling scope and also improves M223 exact source; M248 failure is PPO gradient conflict or insufficient protected-source pressure

## Hypothesis

M248 failed because PPO rollout gradients and anchors still overpower or conflict with the protected-key source loss. A source-only optimization probe should distinguish implementation/steerability from PPO gradient conflict.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt, runs/ppo_m248_source_balanced_from_m239_seed5224/checkpoint.pt
- parent_dataset: runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz, runs/m231_protected_key_snippet_surface/protected_key_snippets.npz, runs/m248_source_aware_exact_m232_eval/source_summary.csv
- parent_config: configs/ppo_m248_source_balanced_from_m239_smoke.json
- parent_objective: protected-key source exact objective, source-balanced PPO gradient pressure
- derived_from: m248-source-balanced-ppo-smoke-from-m239
- blocked_by: m248-source-balanced-ppo-smoke-from-m239
- supersedes: None
- invalidates: None

## Success Criteria

- measure whether the protected-key source loss can decrease from M239 under source-only optimization
- measure whether the M223 source loss is affected by that source-only update
- compare source-only movement against M248 PPO movement
- choose one bounded next repair before more PPO
- keep M239 alpha 0.5 as current public-gate base

## Failure Criteria

- run PPO before the audit
- repeat M248 with larger coefficients without gradient evidence
- ignore protected-key source deltas
- change the actor input contract

## Evidence Gates

- M248 source-aware exact reports
- protected-key source-only optimization probe
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M249
- do not change actor inputs
- do not loosen protected-key source gate
- do not repeat M248 before understanding the protected-key source gradient

## Failure Taxonomy

- none

## Scoreboard

- milestone: m249-protected-key-source-gradient-audit
- type: gate
- checkpoint: runs/m249_protected_key_source_actor_coupling_probe/optimized_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_protected_key_source_actor_coupling_calibration
- reason: M249 shows protected-key source loss is strongly steerable in actor-coupling scope and also improves M223 exact source; M248 failure is PPO gradient conflict or insufficient protected-source pressure

## Next Blocker

Interpolate protected-source calibration and gate it.
