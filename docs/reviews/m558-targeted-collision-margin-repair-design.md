# m558-targeted-collision-margin-repair-design Research Review

## Summary

- Generated at UTC: 20260524T050225Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: targeted_collision_margin_repair_design_admit_m559_config_family
- Decision reason: M558 designs a collision and clearance-margin reward branch with fresh route-screen seed 16560 and no actor input changes

## Hypothesis

A targeted collision/margin repair design can address the M557 failure mode by rewarding clearance and penalizing obstacle contact while avoiding overfit to the M556 route-screen seed block.

## Lineage

- parent_checkpoint: runs/m556_l3_repair_epoch1_clip01_seed3540/checkpoints/checkpoint_step_256.pt, runs/m556_l3_repair_longseq_epoch1_seed3540/checkpoints/checkpoint_step_512.pt, runs/m556_l3_repair_lowentropy_epoch1_seed3540/checkpoints/checkpoint_step_256.pt
- parent_dataset: docs/m557-m556-route-screen-failure-audit.md, runs/m557_m556_route_screen_failure_audit/summary.json
- parent_config: configs/ppo_m555_l3_repair_epoch1_clip01_4096.json, configs/ppo_m555_l3_repair_longseq_epoch1_4096.json, configs/ppo_m555_l3_repair_lowentropy_epoch1_4096.json
- parent_objective: design targeted collision and clearance-margin repair after M556 route-screen rejection
- derived_from: m557-m556-route-screen-failure-audit
- blocked_by: m557-m556-route-screen-failure-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design states which reward or PPO controls may change
- design rotates the next route-screen seed and keeps M556 as diagnostic only
- design defines pass/fail conditions before more training
- research validation passes

## Failure Criteria

- design simply repeats M555 PPO stability variants
- design uses M556 route-screen rows as selection data again
- design changes actor input contract

## Evidence Gates

- design collision/margin repair without changing actor inputs
- rotate route-screen v2 seed before any new selection
- preserve L0/L2 references and no-public-row provenance
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train directly on M556 route-screen seeds as the next selection gate
- do not weaken collision or margin route-screen thresholds
- do not add privileged actor inputs
- do not run public frozen-source diagnostics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m558-targeted-collision-margin-repair-design
- type: infrastructure
- checkpoint: docs/m558-targeted-collision-margin-repair-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: targeted_collision_margin_repair_design_admit_m559_config_family
- reason: M558 designs a collision and clearance-margin reward branch with fresh route-screen seed 16560 and no actor input changes

## Next Blocker

m559-targeted-collision-margin-config-family
