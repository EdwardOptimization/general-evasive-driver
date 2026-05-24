# m555-l3-repair-v2-config-family Research Review

## Summary

- Generated at UTC: 20260524T045030Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: l3_repair_v2_config_family_pass_admit_m556_route_screen_selection
- Decision reason: M555 adds epoch1_clip01 longseq_epoch1 and lowentropy_epoch1 L3-only configs while preserving M548 L3 env and P0 contract

## Hypothesis

A small L3-only config family that changes only PPO stability controls can test whether recurrent policy drift, not the P0 input contract, caused the M544-M550 L3 repair failure.

## Lineage

- parent_checkpoint: runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m554-route-screen-gated-l3-repair-v2-design.md
- parent_config: configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json
- parent_objective: implement route-screen-gated L3 recurrent repair v2 config family
- derived_from: m554-route-screen-gated-l3-repair-v2-design
- blocked_by: m554-route-screen-gated-l3-repair-v2-design
- supersedes: None
- invalidates: None

## Success Criteria

- configs implement epoch1_clip01, longseq_epoch1, and lowentropy_epoch1
- tests verify the env section matches M548 L3 exactly
- tests verify only M554-approved PPO keys differ
- research validation passes

## Failure Criteria

- configs alter task distribution or actor input contract
- configs omit update-aligned checkpointing
- tests cannot distinguish approved PPO changes from hidden env changes

## Evidence Gates

- add only the M554-approved L3 PPO-stability config variants
- preserve M548 L3 env/task/P0 actor input contract
- keep checkpoint_interval_steps = 256 for route-screen v2 selection
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not change env sampler or reward terms
- do not add privileged actor inputs
- do not add more config variants than M554 approved
- do not run public frozen-source eval

## Failure Taxonomy

- none

## Scoreboard

- milestone: m555-l3-repair-v2-config-family
- type: infrastructure
- checkpoint: configs/ppo_m555_l3_repair_epoch1_clip01_4096.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_repair_v2_config_family_pass_admit_m556_route_screen_selection
- reason: M555 adds epoch1_clip01 longseq_epoch1 and lowentropy_epoch1 L3-only configs while preserving M548 L3 env and P0 contract

## Next Blocker

m556-l3-repair-v2-route-screen-selection
