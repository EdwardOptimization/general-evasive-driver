# m800-v4-low-margin-source-diverse-corpus-refresh-design Research Review

## Summary

- Generated at UTC: 20260525T045625Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: low_margin_corpus_refresh_design_admit_m801
- Decision reason: M800 designs a no-training boundary-retargeted low-margin corpus refresh with strict primary margin source-diversity and dominance gates before any further active-steer calibration

## Hypothesis

A dedicated source-diverse low-margin corpus refresh can provide enough near-boundary normal rows to fairly test active-steer residual guarding without overfitting to the single public active source.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m799-v4-active-steer-guard-calibration-audit.md, docs/m798-v4-active-steer-guard-calibration-implementation.md, runs/m798_v4_active_steer_guard_calibration/summary.json, runs/m798_v4_active_steer_guard_calibration/low_margin_guard_rows.csv, runs/m798_v4_active_steer_guard_calibration/separability_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/replay_rows.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m799-v4-active-steer-guard-calibration-audit.json
- parent_objective: design a source-diverse low-margin normal-boundary corpus refresh
- derived_from: m799-v4-active-steer-guard-calibration-audit
- blocked_by: m798-v4-active-steer-guard-calibration-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M800 documents a no-training corpus refresh design
- M800 specifies measurable row, seed, source_index, fault-family, and dominance gates
- M800 specifies outputs for candidates, accepted rows, and summary
- M800 preserves actor and residual-head input contracts
- M800 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- design weakens the M798 source-diversity blocker
- design optimizes only seed 77025 source_index 12
- design lacks measurable corpus acceptance targets
- design uses private holdout feedback for public tuning
- design admits training, PPO, or promotion

## Evidence Gates

- M800 designs only; it does not implement or train
- M800 preserves the P0 human-view actor contract
- M800 targets source-diverse low-margin normal-boundary coverage
- M800 caps the known active public source instead of optimizing only it
- M800 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not implement the corpus miner
- do not train any parameters
- do not run closed-loop replay as a result claim
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken low-margin source-diversity thresholds
- do not tune only seed 77025 source_index 12
- do not use private holdout failures to tune the public corpus

## Failure Taxonomy

- scenario_sampling_failure
- objective_overfit
- private_holdout_contamination

## Scoreboard

- milestone: m800-v4-low-margin-source-diverse-corpus-refresh-design
- type: infrastructure
- checkpoint: docs/m800-v4-low-margin-source-diverse-corpus-refresh-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: low_margin_corpus_refresh_design_admit_m801
- reason: M800 designs a no-training boundary-retargeted low-margin corpus refresh with strict primary margin source-diversity and dominance gates before any further active-steer calibration

## Next Blocker

m801-v4-low-margin-source-diverse-corpus-refresh-implementation
