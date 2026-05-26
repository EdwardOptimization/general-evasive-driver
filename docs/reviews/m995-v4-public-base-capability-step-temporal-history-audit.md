# m995-v4-public-base-capability-step-temporal-history-audit Research Review

## Summary

- Generated at UTC: 20260526T144612Z
- Type: gate
- Gate tier: process
- Promotion decision: route_to_temporal_sequence_corpus_export_design
- Decision reason: M995 audits M994 as temporal-history positive but not cross-fault positive and routes to exact-auditable temporal sequence corpus export design

## Hypothesis

M994 provides useful temporal-history evidence, but the project must audit claim scope and route before exporting a corpus or training.

## Lineage

- parent_checkpoint: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
- parent_dataset: docs/m994-v4-public-base-capability-step-sequence-intervention-probe.md, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/summary.json, runs/m994_v4_public_base_capability_step_sequence_intervention_probe/accepted_sequence_rows.csv
- parent_config: experiments/manifests/m994-v4-public-base-capability-step-sequence-intervention-probe.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: audit temporal-history-positive sequence evidence before corpus export or objective design
- derived_from: m994-v4-public-base-capability-step-sequence-intervention-probe, m993-v4-public-base-capability-step-sequence-intervention-design
- blocked_by: M994 is temporal-history positive but cross-fault sequence variants have zero accepted rows
- supersedes: None
- invalidates: calling M994 cross-fault wrong-history positive, running PPO directly from M994

## Success Criteria

- audit artifact exists
- temporal and cross-fault evidence are separated
- source diversity of accepted temporal rows is summarized
- route decision is explicit
- no training or PPO occurs

## Failure Criteria

- audit artifact is missing
- M994 is overclaimed as cross-fault positive
- route decision is missing
- training or PPO starts
- hidden event labels enter actor observations

## Evidence Gates

- M995 must not run PPO
- M995 must not promote
- M995 must not change actor inputs
- M995 must separate temporal-history evidence from cross-fault wrong-history evidence
- M995 must choose a route before objective training

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add hidden event labels to actor observations
- do not train or optimize
- do not use private holdout
- do not claim true per-wheel/asymmetric faults
- do not call M994 cross-fault positive
- do not proceed to PPO

## Failure Taxonomy

- none

## Scoreboard

- milestone: m995-v4-public-base-capability-step-temporal-history-audit
- type: gate
- checkpoint: docs/m995-v4-public-base-capability-step-temporal-history-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_to_temporal_sequence_corpus_export_design
- reason: M995 audits M994 as temporal-history positive but not cross-fault positive and routes to exact-auditable temporal sequence corpus export design

## Next Blocker

m996-v4-public-base-temporal-sequence-corpus-export-design
