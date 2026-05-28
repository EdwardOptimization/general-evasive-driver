# m1377-paper-route-promoted-base-source-rich-sequence-intervention-probe Research Review

## Summary

- Generated at UTC: 20260528T215353Z
- Type: gate
- Gate tier: generalization
- Promotion decision: promoted_base_source_rich_sequence_probe_temporal_positive_seed_thin_route_to_audit
- Decision reason: M1377 sequence probe finds 180 temporal accepted rows across 8 fault pairs but only 9 accepted seeds and zero cross-fault accepted rows

## Hypothesis

M1375 reset-only source rows can expose temporal-history dependence for the promoted M1362 base under sequence-level interventions.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1376-paper-route-promoted-base-source-rich-public-wave-result-audit.md, runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv, runs/m1375_promoted_base_source_rich_public_wave/summary.json, docs/m994-v4-public-base-capability-step-sequence-intervention-probe.md
- parent_config: experiments/manifests/m1376-paper-route-promoted-base-source-rich-public-wave-result-audit.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: probe sequence-level temporal interventions on M1375 reset-only source rows for the promoted M1362 base
- derived_from: m1376-paper-route-promoted-base-source-rich-public-wave-result-audit
- blocked_by: M1375 larger source-rich wave remains cross-fault sparse but has 1281 reset-only rows
- supersedes: continuing seed-only cross-fault scaling without a new intervention axis, training directly from sparse M1375 accepted rows, treating reset-only rows as wrong-history proof
- invalidates: None

## Success Criteria

- runs/m1377_promoted_base_source_rich_sequence_intervention_probe/summary.json exists
- selected_source_rows > 0
- intervention_rows > 0
- actor_parameters_changed == false
- training_started == false
- ppo_used == false
- promoted == false
- accepted_temporal_sequence_rows and accepted_cross_fault_sequence_rows are reported separately
- variant and history-length summaries exist

## Failure Criteria

- summary or core sequence CSV artifacts are missing
- selected_source_rows or intervention_rows is zero
- actor parameters or actor inputs change
- training, PPO, promotion, private holdout, corpus export, or objective update occurs
- temporal positives are reported as cross-fault self-identification

## Evidence Gates

- M1377 must run no-training sequence intervention probe on M1375 reset-only rows
- M1377 must keep actor inputs and checkpoint parameters unchanged
- M1377 must separate temporal accepted rows from cross-fault accepted rows
- M1377 must keep private holdout unused
- M1377 must not export training corpus or run objective updates

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not mutate the candidate checkpoint
- do not call temporal-history positives cross-fault self-identification
- do not export an objective corpus without a separate design/audit
- do not claim true high-fidelity per-wheel physics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1377-paper-route-promoted-base-source-rich-sequence-intervention-probe
- type: gate
- checkpoint: runs/m1377_promoted_base_source_rich_sequence_intervention_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_sequence_probe_temporal_positive_seed_thin_route_to_audit
- reason: M1377 sequence probe finds 180 temporal accepted rows across 8 fault pairs but only 9 accepted seeds and zero cross-fault accepted rows

## Next Blocker

m1378-paper-route-promoted-base-source-rich-sequence-probe-result-audit
