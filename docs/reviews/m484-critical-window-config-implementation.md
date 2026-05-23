# m484-critical-window-config-implementation Research Review

## Summary

- Generated at UTC: 20260523T223952Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: critical_window_configs_sampling_pass_admit_m485_matched_current_mining
- Decision reason: M484 adds two critical-window configs; both pass 384-reset sampling stress with 3 labels and M399 behavior smokes complete without proof mining

## Hypothesis

Critical-window zero-relvel configs can be sampled robustly and create a harder but non-saturated diagnostic distribution before source-diverse tail-aligned proof mining.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m482_tail_aligned_wrong_history_gate/summary.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m483-critical-window-config-design.json
- parent_objective: critical-window config implementation and sampling validation
- derived_from: m483-critical-window-config-design
- blocked_by: m483-critical-window-config-design
- supersedes: None
- invalidates: None

## Success Criteria

- both configs are added and parse successfully
- sampling stress has zero sampling failures across pre-registered seed blocks
- each config has at least two obstacle labels and single-label share <= 0.80
- small M399 behavior smoke completes
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- either config fails to sample robustly
- either config is single-label dominated beyond threshold
- behavior smoke is trivially saturated or broken
- training or checkpoint promotion is performed

## Evidence Gates

- add critical-window near-threshold zero-relvel config
- add critical-window late high-energy zero-relvel config
- run reset/sampling stress before proof mining
- run small M399 behavior smoke if sampling passes
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not add privileged actor inputs
- do not run proof mining before sampling stress passes
- do not count M482 single-source events as proof
- do not tune from private holdouts

## Failure Taxonomy

- none

## Scoreboard

- milestone: m484-critical-window-config-implementation
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: critical_window_configs_sampling_pass_admit_m485_matched_current_mining
- reason: M484 adds two critical-window configs; both pass 384-reset sampling stress with 3 labels and M399 behavior smokes complete without proof mining

## Next Blocker

m485-critical-window-matched-current-mining
