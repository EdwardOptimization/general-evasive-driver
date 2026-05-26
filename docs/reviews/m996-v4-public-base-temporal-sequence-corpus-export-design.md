# m996-v4-public-base-temporal-sequence-corpus-export-design Research Review

## Summary

- Generated at UTC: 20260526T145622Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_sequence_corpus_export_design_admit_m997
- Decision reason: M996 designs a no-training exact-auditable temporal sequence corpus export with temporal positives diagnostic-only cross-fault rows weighting and objective sanity gates

## Hypothesis

M994 temporal accepted rows can be converted into a structured, exact-auditable sequence corpus without changing actor inputs or overclaiming cross-fault self-ID.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m995-v4-public-base-capability-step-temporal-history-audit.md, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/accepted_sequence_rows.csv
- parent_config: experiments/manifests/m995-v4-public-base-capability-step-temporal-history-audit.json, experiments/manifests/m994-v4-public-base-capability-step-sequence-intervention-probe.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: design an exact-auditable temporal sequence corpus export for M994 temporal accepted rows
- derived_from: m995-v4-public-base-capability-step-temporal-history-audit, m994-v4-public-base-capability-step-sequence-intervention-probe
- blocked_by: M995 routes source-diverse temporal-history evidence to corpus export design while cross-fault positives remain absent
- supersedes: None
- invalidates: training directly from M994 CSV metrics, treating cross-fault zero variants as positive targets

## Success Criteria

- design artifact exists
- positive rows are limited to reset_then_warm_history and delayed_capability_history
- cross-fault/action-response mismatch zero variants are diagnostic-only
- schema includes normal/variant observations, hidden states, actions, masks, gaps, and source metadata
- exact objective sanity and source-diversity gates are defined
- no training or PPO occurs

## Failure Criteria

- design artifact is missing
- cross-fault zero variants are treated as positive targets
- hidden event labels enter actor observations
- exact objective sanity is omitted
- training or PPO starts
- promotion occurs

## Evidence Gates

- M996 must not run PPO
- M996 must not promote
- M996 must not change actor inputs
- M996 must design exact objective sanity before any objective update
- M996 must keep cross-fault zero variants diagnostic-only

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize actor parameters
- do not use private holdout
- do not claim cross-fault wrong-history self-identification
- do not export cross-fault zero variants as positives
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m996-v4-public-base-temporal-sequence-corpus-export-design
- type: infrastructure
- checkpoint: docs/m996-v4-public-base-temporal-sequence-corpus-export-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_corpus_export_design_admit_m997
- reason: M996 designs a no-training exact-auditable temporal sequence corpus export with temporal positives diagnostic-only cross-fault rows weighting and objective sanity gates

## Next Blocker

m997-v4-public-base-temporal-sequence-corpus-export-implementation
