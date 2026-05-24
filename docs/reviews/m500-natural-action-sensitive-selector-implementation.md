# m500-natural-action-sensitive-selector-implementation Research Review

## Summary

- Generated at UTC: 20260524T000821Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M500 finds targeted trajectory mean 0.228 but only 171 targeted rows with single-config share 0.725 and normal margin min 0.932 so action-sensitive rows are high-margin/source-limited

## Hypothesis

The full M495 natural belief surface contains source-diverse rows where one-shot wrong-history produces materially larger short-horizon action trajectory differences than the M496 targeted subset.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m495_natural_belief_matched_current_summary/combined_matched_pairs.csv, runs/m498_natural_belief_wrong_history_no_effect_audit/summary.json
- parent_config: configs/m494_natural_belief_short_reveal_zero_relvel.json, configs/m494_natural_belief_warmup_capability_zero_relvel.json, experiments/manifests/m499-natural-belief-action-sensitive-selector-design.json
- parent_objective: natural action-sensitive wrong-history selector implementation
- derived_from: m499-natural-belief-action-sensitive-selector-design
- blocked_by: m499-natural-belief-action-sensitive-selector-design
- supersedes: None
- invalidates: None

## Success Criteria

- selector implementation is tested
- selector run completes on the full M495 surface
- targeted_pair_count >= 240 if an action-sensitive surface exists
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

- implementation cannot reconstruct needed snapshots
- selector finds no source-diverse action-sensitive surface
- selected rows remain at M498-level weak trajectory distances
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- implement natural_wrong_history_action_sensitive_selector
- run it on the full M495 matched-current surface
- export action-sensitive candidate and targeted pair artifacts
- require source diversity before admitting another outcome gate
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not repeat M496 target-z triage unchanged
- do not tune from private holdouts

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m500-natural-action-sensitive-selector-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_outcome_gate_admission
- reason: M500 finds targeted trajectory mean 0.228 but only 171 targeted rows with single-config share 0.725 and normal margin min 0.932 so action-sensitive rows are high-margin/source-limited

## Next Blocker

M501 should audit and redesign the natural task or selector because M500 found stronger action trajectory rows but not a source-diverse or near-boundary action-sensitive surface.
