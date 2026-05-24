# m560-collision-margin-route-screen-selection Research Review

## Summary

- Generated at UTC: 20260524T051124Z
- Type: gate
- Gate tier: generalization
- Promotion decision: collision_margin_route_screen_reject_admit_l2_to_l3_distillation_design
- Decision reason: M560 rejects public diagnostics because no reward-shaping L3 checkpoint clears fresh route-screen v2; candidates pass success but fail margin and collision checks

## Hypothesis

Targeted collision and clearance-margin reward variants may produce an L3 checkpoint that clears fresh route-screen v2 against L0 without relying on M556 route-screen overfit.

## Lineage

- parent_checkpoint: runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m558-targeted-collision-margin-repair-design.md, docs/m559-targeted-collision-margin-config-family.md
- parent_config: configs/ppo_m559_l3_collision35_terminal4_4096.json, configs/ppo_m559_l3_collision35_dense002_4096.json, configs/ppo_m559_l3_collision45_terminal4_4096.json
- parent_objective: train M559 configs and select checkpoints with route-screen v2 fresh seed 16560
- derived_from: m559-targeted-collision-margin-config-family
- blocked_by: m559-targeted-collision-margin-config-family
- supersedes: None
- invalidates: None

## Success Criteria

- all three M559 training runs complete with valid P0 L3 metadata
- route-screen v2 uses fresh seed 16560 and no public frozen-source rows
- decision records whether public diagnostics are admitted or blocked
- research validation passes

## Failure Criteria

- training run fails or metadata is invalid
- route-screen selection uses seed 15560 instead of fresh seed 16560
- no candidate clears L0 route-screen v2

## Evidence Gates

- train all three M559 configs on seed 3540
- evaluate all interval/final checkpoints with route-screen v2 seed 16560
- include L0/L2 references and level-matched env configs
- do not use M556 seed 15560 as the selection gate
- do not run public frozen-source diagnostics unless route-screen v2 admits a candidate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not select from M556 diagnostic route-screen seed
- do not weaken collision or margin thresholds
- do not change actor input contract during training
- do not run public frozen-source diagnostics before route-screen pass

## Failure Taxonomy

- training_instability
- promotion_gate_failure

## Scoreboard

- milestone: m560-collision-margin-route-screen-selection
- type: gate
- checkpoint: runs/m560_collision_margin_route_screen_selection/summary.json
- success_rate: 0.125
- termination_rate: 0.875
- clearance_margin_mean: 0.013326
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: collision_margin_route_screen_reject_admit_l2_to_l3_distillation_design
- reason: M560 rejects public diagnostics because no reward-shaping L3 checkpoint clears fresh route-screen v2; candidates pass success but fail margin and collision checks

## Next Blocker

m561-l2-to-l3-distillation-design
