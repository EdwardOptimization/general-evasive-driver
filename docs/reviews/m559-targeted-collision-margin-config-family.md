# m559-targeted-collision-margin-config-family Research Review

## Summary

- Generated at UTC: 20260524T050640Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: collision_margin_config_family_pass_admit_m560_route_screen_selection
- Decision reason: M559 adds three collision and clearance-margin reward configs while preserving M555 epoch1_clip01 PPO controls and P0 actor inputs

## Hypothesis

A small collision/margin reward config family can test whether obstacle-contact shaping repairs the M557 route-screen failure without changing driver inputs.

## Lineage

- parent_checkpoint: runs/m556_l3_repair_epoch1_clip01_seed3540/checkpoints/checkpoint_step_256.pt
- parent_dataset: docs/m558-targeted-collision-margin-repair-design.md
- parent_config: configs/ppo_m555_l3_repair_epoch1_clip01_4096.json
- parent_objective: implement targeted collision and clearance-margin repair configs
- derived_from: m558-targeted-collision-margin-repair-design
- blocked_by: m558-targeted-collision-margin-repair-design
- supersedes: None
- invalidates: None

## Success Criteria

- configs implement collision35_terminal4, collision35_dense002, and collision45_terminal4
- tests verify only M558-approved obstacle reward fields differ from M555 epoch1_clip01
- tests verify P0 L3 actor contract and checkpoint cadence remain unchanged
- research validation passes

## Failure Criteria

- configs alter actor inputs or hidden/oracle fields
- configs alter unapproved task randomization fields
- tests cannot isolate reward changes

## Evidence Gates

- add only the M558-approved collision/margin reward config variants
- preserve P0 actor input contract and M555 epoch1_clip01 PPO controls
- preserve update-aligned checkpointing
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not add privileged actor inputs
- do not change route-screen thresholds
- do not add more reward variants than M558 approved
- do not run public frozen-source diagnostics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m559-targeted-collision-margin-config-family
- type: infrastructure
- checkpoint: configs/ppo_m559_l3_collision35_terminal4_4096.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: collision_margin_config_family_pass_admit_m560_route_screen_selection
- reason: M559 adds three collision and clearance-margin reward configs while preserving M555 epoch1_clip01 PPO controls and P0 actor inputs

## Next Blocker

m560-collision-margin-route-screen-selection
