# m552-route-screen-v2-retrospective Research Review

## Summary

- Generated at UTC: 20260524T043707Z
- Type: gate
- Gate tier: process
- Promotion decision: route_screen_v2_rejects_m549_admit_m553_runner
- Decision reason: M552 route-screen v2 rejects M549 selected L3 before public eval because success is below L0 and far below L2

## Hypothesis

A stronger public-neutral route-screen v2 should reject the M549 selected checkpoint before public frozen-source diagnostics, preventing the M550 failure pattern.

## Lineage

- parent_checkpoint: runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: docs/m551-route-health-screen-redesign.md, runs/m550_m549_public_surface_diagnostic_aggregate/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json, configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json
- parent_objective: retrospectively test whether route-screen v2 would reject M549 selected checkpoint before public eval
- derived_from: m551-route-health-screen-redesign
- blocked_by: m551-route-health-screen-redesign
- supersedes: None
- invalidates: None

## Success Criteria

- route-screen v2 artifacts compare all four checkpoints on the same route seeds
- decision clearly states whether M549 selected checkpoint would have been rejected
- failure is classified if route-screen v2 still admits the public-failing checkpoint
- research validation passes

## Failure Criteria

- screen uses public frozen-source rows
- screen uses fewer than 64 episodes
- screen lacks L0 and L2 references

## Evidence Gates

- evaluate L0, L2, original L3, and M549 selected L3 on a public-neutral route distribution
- use at least 64 episodes and obstacle/collision/margin metrics from autodrift.evaluate
- apply M551 route-screen v2 rule without public frozen-source rows
- do not train or promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use M550 public frozen-source rows as selection data
- do not change route-screen v2 thresholds after seeing retrospective result
- do not promote checkpoint from route-screen evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m552-route-screen-v2-retrospective
- type: gate
- checkpoint: runs/m552_route_screen_v2_retrospective/summary.json
- success_rate: 0.046875
- termination_rate: 0.953125
- clearance_margin_mean: 0.213472
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: route_screen_v2_rejects_m549_admit_m553_runner
- reason: M552 route-screen v2 rejects M549 selected L3 before public eval because success is below L0 and far below L2

## Next Blocker

m553-route-screen-v2-runner-implementation
