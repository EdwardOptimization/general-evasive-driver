# m919-v4-public-base-expanded-target-regeneration-implementation Research Review

## Summary

- Generated at UTC: 20260525T214931Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_expanded_target_regeneration_pass_route_to_residual_objective_design
- Decision reason: M919 passes expanded target generation with 122 accepted targets 103 strict low-tail targets 26 seeds 14 fault-family pairs and max pair fraction 0.197 without actor changes

## Hypothesis

A coverage-first near-tail expansion can provide at least 96 source-diverse M399-rooted targets while preserving actor immutability and blocking training/replay/PPO/promotion.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m918-v4-public-base-target-source-expansion-design.md, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv, runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
- parent_config: experiments/manifests/m918-v4-public-base-target-source-expansion-design.json
- parent_objective: implement no-training expanded near-tail target regeneration for M399 public base
- derived_from: m918-v4-public-base-target-source-expansion-design
- blocked_by: expanded source target generation has not yet been run
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- source_candidate_rows.csv exists
- accepted_target_rows.csv exists
- accepted_targets >= 96
- strict_low_tail_accepted_targets >= 60
- distinct_fault_family_pairs >= 10
- distinct_seeds >= 24
- max_fault_family_pair_fraction <= 0.25
- training_started and ppo_used are false
- promoted is false

## Failure Criteria

- M919 trains or mutates actor parameters
- accepted_targets < 96
- strict_low_tail_accepted_targets < 60
- distinct_fault_family_pairs < 10
- distinct_seeds < 24
- max_fault_family_pair_fraction > 0.25
- M919 runs M880 exact compatibility, replay, PPO, or promotion

## Evidence Gates

- M919 must not train
- M919 must keep actor parameters unchanged
- M919 must export source candidate selected candidate-action accepted rejected and group artifacts
- M919 must enforce expanded source diversity gates
- M919 must block residual training, M880 exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M919
- do not update actor parameters
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not treat near-tail target mining as a deploy-time rule

## Failure Taxonomy

- none

## Scoreboard

- milestone: m919-v4-public-base-expanded-target-regeneration-implementation
- type: infrastructure
- checkpoint: runs/m919_v4_public_base_expanded_target_regeneration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_expanded_target_regeneration_pass_route_to_residual_objective_design
- reason: M919 passes expanded target generation with 122 accepted targets 103 strict low-tail targets 26 seeds 14 fault-family pairs and max pair fraction 0.197 without actor changes

## Next Blocker

expanded public-base target regeneration has not yet been run
