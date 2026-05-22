# m242-exact-outcome-objective-evaluator Research Review

## Summary

- Generated at UTC: 20260522T140348Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_exact_gated_ppo_smoke_from_m239
- Decision reason: M242 adds outcome_intervention_eval --exact with deterministic full-corpus loss mode-tagged outputs focused tests and M232/M223 exact smoke; no PPO and no driver promotion

## Hypothesis

Small M232/M223 corpora need a deterministic full-corpus outcome objective evaluator. Adding it to the harness will make future PPO/interpolation promotion decisions less sensitive to sampled fixed-batch noise.

## Lineage

- parent_checkpoint: runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
- parent_dataset: runs/m232_combined_m223_m231_snippet_anchor/outcome_intervention_snippets.npz, runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.npz
- parent_config: configs/ppo_m237_trajectory_anchor_from_m224_smoke.json, configs/ppo_m240_trajectory_anchor_from_m224_smoke.json
- parent_objective: deterministic full-corpus outcome objective, fixed-batch outcome objective reliability
- derived_from: m241-trajectory-ppo-seed-direction-audit
- blocked_by: m240-interpolation-guarded-ppo-repeat-from-m224
- supersedes: None
- invalidates: None

## Success Criteria

- implement an exact full-corpus outcome objective evaluation path
- cover exact evaluation with tests
- reproduce the M241 exact-loss comparison for M224 M237 M239 and M240
- do not run PPO
- pre-register the next bounded PPO or objective-direction screen after the evaluator exists

## Failure Criteria

- run PPO
- change actor inputs
- silently mix sampled and exact objective metrics
- remove existing fixed-batch evaluator compatibility

## Evidence Gates

- exact full-corpus objective unit tests
- M232/M223 exact objective smoke
- research validator

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO in M242
- do not change actor inputs
- do not replace proof gates with objective values
- do not use sampled fixed-batch objective as the only promotion signal for tiny corpora

## Failure Taxonomy

- none

## Scoreboard

- milestone: m242-exact-outcome-objective-evaluator
- type: infrastructure
- checkpoint: None
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_exact_gated_ppo_smoke_from_m239
- reason: M242 adds outcome_intervention_eval --exact with deterministic full-corpus loss mode-tagged outputs focused tests and M232/M223 exact smoke; no PPO and no driver promotion

## Next Blocker

Run one exact-objective-gated PPO smoke from the M239 public-gate base.
