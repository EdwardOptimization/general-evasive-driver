# m495-natural-belief-matched-current-mining Research Review

## Summary

- Generated at UTC: 20260523T234233Z
- Type: gate
- Gate tier: proof
- Promotion decision: natural_belief_matched_surface_pass_admit_m496_targeted_pair_triage
- Decision reason: M495 combined matched-current surface has 5580 accepted pairs across 6 seeds 3 labels 3 targets and 2 configs with single-seed share 0.175 and single-label share 0.480

## Hypothesis

The M494 natural belief decision-window configs can produce source-diverse matched-current ambiguity surfaces where current ego/scene can be similar while pre-reveal command-response histories imply different capability.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m494_natural_belief_decision_config_validation/sampling_summary.json, runs/m494_natural_belief_decision_config_validation/behavior_summary.json
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m494-natural-belief-decision-config-implementation.json
- parent_objective: natural belief matched-current ambiguity mining
- derived_from: m494-natural-belief-decision-config-implementation
- blocked_by: m494-natural-belief-decision-config-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- matched-current mining completes on both configs without sampling failure
- combined accepted_pair_count >= 512
- combined probe_seed_count >= 6
- combined obstacle_label_count >= 2
- combined target_count >= 2
- combined config_count >= 2
- combined single_seed_share <= 0.50
- combined single_label_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- either config cannot produce enough matched-current candidates
- candidate surface is source-narrow
- only one obstacle label or target dominates
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run matched-current mining on both M494 natural belief configs
- require source-diverse candidate surfaces before wrong-history proof gates
- report accepted pairs, physical pairs, labels, targets, seed windows, visible distance, and target z delta
- do not train or promote checkpoint
- do not run private holdout tuning

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not skip source-diversity checks before natural wrong-history gates
- do not count aggregate behavior smoke as self-ID proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m495-natural-belief-matched-current-mining
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: natural_belief_matched_surface_pass_admit_m496_targeted_pair_triage
- reason: M495 combined matched-current surface has 5580 accepted pairs across 6 seeds 3 labels 3 targets and 2 configs with single-seed share 0.175 and single-label share 0.480

## Next Blocker

pending M495 natural belief matched-current mining
