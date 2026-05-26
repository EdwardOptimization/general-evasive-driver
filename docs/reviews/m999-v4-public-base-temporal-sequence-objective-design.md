# m999-v4-public-base-temporal-sequence-objective-design Research Review

## Summary

- Generated at UTC: 20260526T153450Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_sequence_objective_design_admit_exact_evaluator
- Decision reason: M999 designs a temporal sequence objective with normal-sequence retention temporal preference separation and base-logp anchor before any actor update

## Hypothesis

The M997 corpus can support an exact temporal sequence objective that preserves normal-history behavior while using disrupted temporal histories only as preference/separation evidence.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m998-v4-public-base-capability-step-fault-generation-synthesis.md, runs/m997_v4_public_base_temporal_sequence_corpus_export/summary.json, runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz, runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv
- parent_config: experiments/manifests/m998-v4-public-base-capability-step-fault-generation-synthesis.json
- parent_objective: design an exact temporal sequence preference objective over the M997 corpus
- derived_from: m998-v4-public-base-capability-step-fault-generation-synthesis, m997-v4-public-base-temporal-sequence-corpus-export-implementation
- blocked_by: M998 opens the temporal sequence objective branch and blocks PPO until objective design exists
- supersedes: None
- invalidates: training directly from the M997 corpus without objective design, using diagnostic cross-fault rows as positive targets

## Success Criteria

- design artifact exists
- objective terms are defined
- exact no-update evaluator requirements are defined
- row weighting is specified
- variant histories are not trained toward degraded actions
- public proof/replay gates are specified
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- objective uses diagnostic cross-fault rows as positives
- objective trains variant histories toward degraded actions
- row weights are ignored without justification
- training or PPO starts
- promotion occurs

## Evidence Gates

- M999 must not train
- M999 must not run PPO
- M999 must not promote
- M999 must preserve P0 actor inputs
- M999 must keep cross-fault rows diagnostic-only

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

- milestone: m999-v4-public-base-temporal-sequence-objective-design
- type: infrastructure
- checkpoint: docs/m999-v4-public-base-temporal-sequence-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_objective_design_admit_exact_evaluator
- reason: M999 designs a temporal sequence objective with normal-sequence retention temporal preference separation and base-logp anchor before any actor update

## Next Blocker

m1000-v4-public-base-temporal-sequence-objective-evaluator
