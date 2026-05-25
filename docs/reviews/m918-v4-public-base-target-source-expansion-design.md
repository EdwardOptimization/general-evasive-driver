# m918-v4-public-base-target-source-expansion-design Research Review

## Summary

- Generated at UTC: 20260525T214154Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_target_source_expansion_design_admit_m919
- Decision reason: M918 designs coverage-first near-tail source expansion using M909 objective rows plus M912 strict low-tail labels before any residual training exact replay PPO or promotion

## Hypothesis

The M917 failure should be handled by source expansion from M909 near-base rows, not by weakening diversity gates or training on a concentrated 67-row target file.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m916-v4-public-base-target-regeneration-design.md, runs/m917_v4_public_base_target_regeneration/summary.json, runs/m917_v4_public_base_target_regeneration/accepted_target_rows.csv, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m917-v4-public-base-target-regeneration-implementation.json
- parent_objective: design expanded source pool for M399-rooted target regeneration after M917 strict low-tail diversity failure
- derived_from: m917-v4-public-base-target-regeneration-implementation
- blocked_by: M917 accepted only 67 targets and strict low-tail source has only 21 seeds
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m918-v4-public-base-target-source-expansion-design.md exists
- M918 identifies strict low-tail seed coverage as impossible for M917 gates
- M918 pre-registers expanded near-tail source selection and pass gates for M919
- M918 keeps residual training M880 exact compatibility replay PPO and promotion blocked

## Failure Criteria

- M918 lowers M917 diversity gates without source expansion
- M918 treats M917's 67 targets as sufficient for training
- M918 starts training replay PPO exact compatibility or promotion
- M918 changes actor inputs

## Evidence Gates

- M918 must be design-only
- M918 must route away from strict low-tail-only target generation
- M918 must preserve the P0 human-view actor contract
- M918 must keep residual training, M880 exact compatibility, replay, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower M917 diversity gates to pass
- do not train in M918
- do not update actor parameters
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not treat mined targets as deployed rules

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m918-v4-public-base-target-source-expansion-design
- type: infrastructure
- checkpoint: docs/m918-v4-public-base-target-source-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_target_source_expansion_design_admit_m919
- reason: M918 designs coverage-first near-tail source expansion using M909 objective rows plus M912 strict low-tail labels before any residual training exact replay PPO or promotion

## Next Blocker

m919-v4-public-base-expanded-target-regeneration-implementation
