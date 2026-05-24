# m556-l3-repair-v2-route-screen-selection Research Review

## Summary

- Generated at UTC: 20260524T045526Z
- Type: gate
- Gate tier: generalization
- Promotion decision: l3_repair_v2_route_screen_reject_admit_m557_failure_audit
- Decision reason: M556 rejects public diagnostics because no M555 L3 checkpoint clears route-screen v2; best candidate passes L0 success but fails margin and collision checks

## Hypothesis

At least one M555 PPO-stability L3 variant may produce an interval checkpoint that clears route-screen v2 against L0 before public diagnostics.

## Lineage

- parent_checkpoint: runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m554-route-screen-gated-l3-repair-v2-design.md, docs/m555-l3-repair-v2-config-family.md
- parent_config: configs/ppo_m555_l3_repair_epoch1_clip01_4096.json, configs/ppo_m555_l3_repair_longseq_epoch1_4096.json, configs/ppo_m555_l3_repair_lowentropy_epoch1_4096.json
- parent_objective: train M555 L3 repair-v2 configs and select checkpoints with route-screen v2
- derived_from: m555-l3-repair-v2-config-family
- blocked_by: m555-l3-repair-v2-config-family
- supersedes: None
- invalidates: None

## Success Criteria

- all three training runs complete with valid P0 L3 metadata
- route-screen v2 evaluates all saved interval/final checkpoints with L0/L2 references
- decision records whether public diagnostics are admitted or blocked
- research validation passes

## Failure Criteria

- training run fails or writes invalid metadata
- route-screen v2 cannot evaluate multi-candidate checkpoints
- selection uses public frozen-source rows
- no candidate clears L0 route-screen v2

## Evidence Gates

- train all three M555 configs on seed 3540
- evaluate all interval/final checkpoints as route-screen v2 candidates
- use L0/L2 references with level-matched env configs
- write route-screen v2 artifacts with uses_public_frozen_source_rows = false
- do not run public frozen-source diagnostics unless route-screen v2 admits a candidate

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not select checkpoints by public frozen-source rows
- do not weaken route-screen v2 thresholds
- do not drop L0 or L2 references
- do not change actor input contract during training

## Failure Taxonomy

- training_instability
- promotion_gate_failure

## Scoreboard

- milestone: m556-l3-repair-v2-route-screen-selection
- type: gate
- checkpoint: runs/m556_l3_repair_v2_route_screen_selection/summary.json
- success_rate: 0.109375
- termination_rate: 0.890625
- clearance_margin_mean: -0.051892
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l3_repair_v2_route_screen_reject_admit_m557_failure_audit
- reason: M556 rejects public diagnostics because no M555 L3 checkpoint clears route-screen v2; best candidate passes L0 success but fails margin and collision checks

## Next Blocker

m557-m556-route-screen-failure-audit
