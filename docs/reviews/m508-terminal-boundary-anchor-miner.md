# m508-terminal-boundary-anchor-miner Research Review

## Summary

- Generated at UTC: 20260524T010641Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_outcome_gate_admission
- Decision reason: M508 finds 3246 low-margin anchors and strong action signal mean 0.092899 p90 0.130059 but only 104 source-capped targeted pairs and label share 0.827 so natural anchor mining remains geometry concentrated

## Hypothesis

Mining low-clearance normal-history anchors first will produce a larger source-diverse pool of wrong-history-sensitive boundary rows than selecting from the existing M504 pair table.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m506_terminal_boundary_aware_selector/summary.json, runs/m506_terminal_boundary_aware_selector/terminal_boundary_candidates.csv
- parent_config: configs/m502_natural_boundary_pressure_short_reveal_zero_relvel.json, configs/m502_natural_boundary_pressure_warmup_zero_relvel.json, experiments/manifests/m507-terminal-boundary-anchor-mining-design.json
- parent_objective: terminal-boundary anchor miner
- derived_from: m507-terminal-boundary-anchor-mining-design
- blocked_by: m507-terminal-boundary-anchor-mining-design
- supersedes: None
- invalidates: None

## Success Criteria

- anchor mining runs on both M502 configs
- anchor_count >= 120
- pair_count >= 240
- probe_seed_count >= 6
- obstacle_label_count >= 2
- config_count >= 2
- single_seed_share <= 0.50
- single_label_share <= 0.70
- single_config_share <= 0.70
- rows with normal_min_clearance_margin <= 0.50 >= 40
- rows with normal_min_clearance_margin <= 1.00 >= 100
- targeted_trajectory_mean >= 0.04
- targeted_trajectory_p90 >= 0.08
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- too few low-clearance anchors are found
- wrong-history search around anchors has no action signal
- candidate surface is source-narrow
- actor contract changes
- training or checkpoint promotion is performed

## Evidence Gates

- mine low-clearance normal-history anchor states from M502 configs
- search source-diverse one-shot wrong histories around those anchors
- score short-horizon action and margin effects
- do not run outcome gates, train, or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not use hidden-hold variants as deployable proof
- do not skip source caps
- do not tune from private holdouts

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m508-terminal-boundary-anchor-miner
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_outcome_gate_admission
- reason: M508 finds 3246 low-margin anchors and strong action signal mean 0.092899 p90 0.130059 but only 104 source-capped targeted pairs and label share 0.827 so natural anchor mining remains geometry concentrated

## Next Blocker

M509 should design bounded obstacle-boundary projection because natural anchor-first mining finds anchors and action signal but remains source-capped.
