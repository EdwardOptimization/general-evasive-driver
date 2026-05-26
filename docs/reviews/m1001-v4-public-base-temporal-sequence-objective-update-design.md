# m1001-v4-public-base-temporal-sequence-objective-update-design Research Review

## Summary

- Generated at UTC: 20260526T160016Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_sequence_update_design_admit_exact_probe
- Decision reason: M1001 designs actor_mean-only temporal objective update with exact trust-region gates and no PPO or promotion

## Hypothesis

A tiny objective-only actor_mean update can be designed with exact preflight gates before any implementation or PPO.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m1000-v4-public-base-temporal-sequence-objective-evaluator.md, runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
- parent_config: experiments/manifests/m1000-v4-public-base-temporal-sequence-objective-evaluator.json
- parent_objective: design a tiny objective-only temporal sequence actor update after exact evaluator sanity passes
- derived_from: m1000-v4-public-base-temporal-sequence-objective-evaluator, m999-v4-public-base-temporal-sequence-objective-design
- blocked_by: M1000 passes no-update exact objective sanity and admits update design only
- supersedes: None
- invalidates: running actor update without exact objective acceptance criteria

## Success Criteria

- design artifact exists
- trainable surface is specified
- exact objective acceptance gates are specified
- public replay gates are specified
- rollback criteria are specified
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- trainable surface is too broad
- exact gates are missing
- diagnostic cross-fault rows are positive targets
- training or PPO starts
- promotion occurs

## Evidence Gates

- M1001 must not train
- M1001 must not run PPO
- M1001 must not promote
- M1001 must specify exact objective acceptance gates
- M1001 must preserve P0 actor inputs

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize actor parameters
- do not use private holdout
- do not claim cross-fault wrong-history self-ID
- do not train variant histories toward degraded actions
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1001-v4-public-base-temporal-sequence-objective-update-design
- type: infrastructure
- checkpoint: docs/m1001-v4-public-base-temporal-sequence-objective-update-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_update_design_admit_exact_probe
- reason: M1001 designs actor_mean-only temporal objective update with exact trust-region gates and no PPO or promotion

## Next Blocker

m1002-v4-public-base-temporal-sequence-objective-update-probe
