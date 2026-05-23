# m496-natural-belief-targeted-pair-triage Research Review

## Summary

- Generated at UTC: 20260523T234613Z
- Type: gate
- Gate tier: proof
- Promotion decision: natural_belief_targeted_triage_pass_admit_m497_decision_window_outcome_gate
- Decision reason: M496 exports 294 targeted pairs across 6 seeds 3 labels 3 targets and 2 configs with single-seed share 0.238 single-label share 0.544 and single-config share 0.605

## Hypothesis

The M495 natural belief matched-current surface is large enough to select a balanced targeted wrong-history pair surface for natural outcome proof gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m495_natural_belief_matched_current_summary/combined_summary.json, runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m495-natural-belief-matched-current-mining.json
- parent_objective: source-diverse natural targeted wrong-history pair triage
- derived_from: m495-natural-belief-matched-current-mining
- blocked_by: m495-natural-belief-matched-current-mining
- supersedes: None
- invalidates: None

## Success Criteria

- targeted_pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- target_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- single_config_share <= 0.70
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- targeted surface is too small
- targeted surface is dominated by one seed label target config or obstacle bucket
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- run wrong_history_targeted_pair_triage on the combined M495 matched-current surface
- preserve source diversity across seeds labels targets configs and obstacle buckets
- export targeted pairs for natural wrong-history outcome gates
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not skip targeted source-diversity caps
- do not run outcome gates if triage surface is source-narrow
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m496-natural-belief-targeted-pair-triage
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: natural_belief_targeted_triage_pass_admit_m497_decision_window_outcome_gate
- reason: M496 exports 294 targeted pairs across 6 seeds 3 labels 3 targets and 2 configs with single-seed share 0.238 single-label share 0.544 and single-config share 0.605

## Next Blocker

pending M496 natural belief targeted pair triage
