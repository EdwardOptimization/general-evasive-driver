# m1379-paper-route-promoted-base-source-rich-sequence-expanded-probe Research Review

## Summary

- Generated at UTC: 20260528T220757Z
- Type: gate
- Gate tier: generalization
- Promotion decision: promoted_base_source_rich_sequence_expanded_probe_temporal_positive_seed_thin_route_to_audit
- Decision reason: M1379 expanded sequence probe finds 224 temporal rows across 9 fault pairs but only 10 accepted seeds and zero cross-fault rows

## Hypothesis

Expanding source-row coverage can resolve the M1377 accepted-seed diversity miss while preserving temporal-history positives.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1378-paper-route-promoted-base-source-rich-sequence-probe-result-audit.md, runs/m1375_promoted_base_source_rich_public_wave/reset_only_rows.csv, runs/m1377_promoted_base_source_rich_sequence_intervention_probe/summary.json
- parent_config: experiments/manifests/m1378-paper-route-promoted-base-source-rich-sequence-probe-result-audit.json, configs/m991_capability_step_fault_source_wave.json
- parent_objective: expand source-row coverage to test whether M1377 temporal-positive seed-thin result reaches source-diverse seed coverage
- derived_from: m1378-paper-route-promoted-base-source-rich-sequence-probe-result-audit
- blocked_by: M1377 passes temporal row and fault-pair thresholds but misses accepted-seed threshold
- supersedes: exporting a temporal corpus from seed-thin M1377 evidence, changing temporal-positive thresholds after results, claiming cross-fault self-ID from temporal positives
- invalidates: None

## Success Criteria

- runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json exists
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

- M1379 must run no-training expanded sequence intervention probe on M1375 reset-only rows
- M1379 must keep actor inputs and checkpoint parameters unchanged
- M1379 must separate temporal accepted rows from cross-fault accepted rows
- M1379 must keep private holdout unused
- M1379 must not export training corpus or run objective updates

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

- milestone: m1379-paper-route-promoted-base-source-rich-sequence-expanded-probe
- type: gate
- checkpoint: runs/m1379_promoted_base_source_rich_sequence_expanded_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promoted_base_source_rich_sequence_expanded_probe_temporal_positive_seed_thin_route_to_audit
- reason: M1379 expanded sequence probe finds 224 temporal rows across 9 fault pairs but only 10 accepted seeds and zero cross-fault rows

## Next Blocker

m1380-paper-route-promoted-base-source-rich-sequence-expanded-result-audit
