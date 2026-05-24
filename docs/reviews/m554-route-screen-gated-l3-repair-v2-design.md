# m554-route-screen-gated-l3-repair-v2-design Research Review

## Summary

- Generated at UTC: 20260524T044645Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: route_screen_gated_l3_repair_v2_design_admit_m555_config_family
- Decision reason: M554 freezes P0 env task boundaries restricts L3 repair v2 to PPO stability controls and requires route-screen v2 before public diagnostics

## Hypothesis

A route-screen-gated L3 repair design can prevent another weak recurrent checkpoint from reaching public diagnostics while targeting the L3 training instability found in M544-M550.

## Lineage

- parent_checkpoint: runs/m542_matched_l3_variance_seed3540/checkpoint.pt, runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt
- parent_dataset: docs/m544-l3-variance-recipe-failure-audit.md, docs/m550-m549-public-surface-diagnostic.md, docs/m552-route-screen-v2-retrospective.md, runs/m553_route_screen_v2_runner_reproduce_m552/summary.json
- parent_config: configs/ppo_m541_matched_l3_variance_4096.json, configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json, configs/ppo_m548_l3_repair_lr1e4_ckpt256_4096.json, configs/ppo_m548_l3_repair_lr5e5_ckpt256_4096.json
- parent_objective: design the next recurrent L3 repair branch under route-screen v2 admission
- derived_from: m553-route-screen-v2-runner-implementation
- blocked_by: m553-route-screen-v2-runner-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- design identifies which L3 training variables may change and which remain frozen
- design defines route-screen v2 selection before public diagnostics
- design states failure taxonomy and promotion boundaries
- research validation passes

## Failure Criteria

- design repeats the M548 recipe without addressing route-screen failure
- design selects checkpoints from public frozen-source rows
- design changes actor input contract

## Evidence Gates

- design next L3 recurrent repair branch without changing P0 actor inputs
- require route-screen v2 pass before any public frozen-source diagnostic
- preserve L2 as the finite-window baseline and L0 as the minimum route gate
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use M550 public rows as checkpoint-selection data
- do not weaken route-screen v2 after M552/M553
- do not remove L0 or L2 references
- do not add privileged actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m554-route-screen-gated-l3-repair-v2-design
- type: infrastructure
- checkpoint: docs/m554-route-screen-gated-l3-repair-v2-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_screen_gated_l3_repair_v2_design_admit_m555_config_family
- reason: M554 freezes P0 env task boundaries restricts L3 repair v2 to PPO stability controls and requires route-screen v2 before public diagnostics

## Next Blocker

m555-l3-repair-v2-config-family
