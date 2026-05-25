# m917-v4-public-base-target-regeneration-implementation Research Review

## Summary

- Generated at UTC: 20260525T214154Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_target_regeneration_route_to_source_expansion_design
- Decision reason: M917 accepts 67 of 67 reconstructed strict low-tail targets but fails accepted target seed and source concentration gates because the strict source pool has only 21 seeds

## Hypothesis

No-training local action target mining can find source-diverse M399-rooted targets for the broad low-tail set without actor mutation, replay, PPO, or promotion.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m916-v4-public-base-target-regeneration-design.md, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m916-v4-public-base-target-regeneration-design.json
- parent_objective: implement no-training M399-rooted target regeneration over low-tail states
- derived_from: m916-v4-public-base-target-regeneration-design
- blocked_by: M399-rooted regenerated targets do not yet exist
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- accepted_target_rows.csv exists
- rejected_target_rows.csv exists
- accepted_targets >= 80
- distinct_fault_family_pairs >= 8
- distinct_seeds >= 24
- max_fault_family_pair_fraction <= 0.25
- training_started and ppo_used are false
- promoted is false

## Failure Criteria

- M917 trains or mutates actor parameters
- accepted_targets < 80
- distinct_fault_family_pairs < 8
- max_fault_family_pair_fraction > 0.25
- M917 runs M880 exact compatibility, replay, PPO, or promotion

## Evidence Gates

- M917 must not train
- M917 must keep actor parameters unchanged
- M917 must export selected, candidate, accepted, and rejected target rows
- M917 must enforce source diversity gates
- M917 must block residual training, M880 exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M917
- do not update actor parameters
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not treat mined targets as deployed rules

## Failure Taxonomy

- none

## Scoreboard

- milestone: m917-v4-public-base-target-regeneration-implementation
- type: infrastructure
- checkpoint: runs/m917_v4_public_base_target_regeneration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_target_regeneration_route_to_source_expansion_design
- reason: M917 accepts 67 of 67 reconstructed strict low-tail targets but fails accepted target seed and source concentration gates because the strict source pool has only 21 seeds

## Next Blocker

M399-rooted target regeneration has not yet been run
