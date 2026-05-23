# m494-natural-belief-decision-config-implementation Research Review

## Summary

- Generated at UTC: 20260523T233656Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: natural_belief_configs_sampling_pass_admit_m495_matched_current_mining
- Decision reason: M494 adds short-reveal and warm-up capability configs; both pass 384-reset sampling and smoke nontrivially without proof mining or checkpoint promotion

## Hypothesis

A short-reveal and a warm-up capability-evidence config can create robust natural decision-window tasks where command-response history may matter before current-response correction dominates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m492_tail_action_replay_sufficiency_summary/combined_summary.json
- parent_config: configs/m484_critical_window_near_threshold_zero_relvel.json, configs/m484_critical_window_late_high_energy_zero_relvel.json, experiments/manifests/m493-natural-belief-decision-window-redesign.json
- parent_objective: natural belief decision-window config implementation
- derived_from: m493-natural-belief-decision-window-redesign
- blocked_by: m493-natural-belief-decision-window-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- both config files are created
- each config has 384/384 reset successes across seed blocks 11800 11900 12000 or failures are documented
- at least one config has >=2 labels and single-label share <=0.80
- behavior smokes complete for at least one sampling-valid config
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- configs cannot sample robustly
- label distribution collapses to one label
- behavior smokes are saturated or fail to run
- actor contract changes
- training or proof mining is performed

## Evidence Gates

- implement two P0-compatible natural belief decision-window configs
- run reset sampling stress on seed blocks 11800 11900 12000
- run small behavior smokes for M399 and baselines if sampling passes
- do not mine proof rows or train

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not run proof mining before sampling validation
- do not tune from private holdout

## Failure Taxonomy

- none

## Scoreboard

- milestone: m494-natural-belief-decision-config-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: natural_belief_configs_sampling_pass_admit_m495_matched_current_mining
- reason: M494 adds short-reveal and warm-up capability configs; both pass 384-reset sampling and smoke nontrivially without proof mining or checkpoint promotion

## Next Blocker

pending M494 natural belief decision config implementation
