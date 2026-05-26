# m997-v4-public-base-temporal-sequence-corpus-export-implementation Research Review

## Summary

- Generated at UTC: 20260526T151734Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: temporal_sequence_corpus_export_pass_route_to_branch_synthesis
- Decision reason: M997 exports 277 temporal positive rows with replay and exact sanity passing and routes to branch synthesis before objective design

## Hypothesis

A no-training exporter can reconstruct M994 temporal accepted rows into exact-auditable sequence tensors with finite sanity metrics and unchanged actor parameters.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m996-v4-public-base-temporal-sequence-corpus-export-design.md, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/accepted_sequence_rows.csv
- parent_config: experiments/manifests/m996-v4-public-base-temporal-sequence-corpus-export-design.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: export M994 temporal positives to a tensor corpus and run exact no-update sanity
- derived_from: m996-v4-public-base-temporal-sequence-corpus-export-design, m995-v4-public-base-capability-step-temporal-history-audit
- blocked_by: M996 requires a no-training corpus exporter before any temporal objective design
- supersedes: None
- invalidates: using M994 metrics-only CSVs as training data

## Success Criteria

- exporter command completes
- temporal_sequence_corpus.npz exists
- metadata.csv and summary.json exist
- row_count == 277
- positive_row_count == 277
- unique_positive_fault_pairs >= 8
- unique_positive_seeds >= 16
- exact no-update sanity is finite
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false

## Failure Criteria

- hidden event labels enter actor observations
- actor parameters change
- training or PPO starts
- promotion occurs
- cross-fault zero variants are exported as positives
- exact no-update sanity fails

## Evidence Gates

- M997 must not run PPO
- M997 must not promote
- M997 must not change actor inputs
- M997 must pass exact no-update sanity
- M997 must keep cross-fault zero variants diagnostic-only

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

- milestone: m997-v4-public-base-temporal-sequence-corpus-export-implementation
- type: infrastructure
- checkpoint: runs/m997_v4_public_base_temporal_sequence_corpus_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: temporal_sequence_corpus_export_pass_route_to_branch_synthesis
- reason: M997 exports 277 temporal positive rows with replay and exact sanity passing and routes to branch synthesis before objective design

## Next Blocker

m998-v4-public-base-capability-step-fault-generation-synthesis
