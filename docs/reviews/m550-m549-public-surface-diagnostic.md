# m550-m549-public-surface-diagnostic Research Review

## Summary

- Generated at UTC: 20260524T042903Z
- Type: gate
- Gate tier: proof
- Promotion decision: public_surface_regression_reject_repair_admit_m551_route_health_redesign
- Decision reason: M550 selected L3 improves over original L3 but remains below L0 and L2 on all public surfaces

## Hypothesis

The M549 route-selected L3 checkpoint may repair the M543 public-surface L3 regression enough to justify a matched repeat, but public diagnostics alone cannot promote it.

## Lineage

- parent_checkpoint: runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m549_update_aligned_l3_route_pilot_summary/summary.json, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv
- parent_config: configs/ppo_m548_l3_repair_fast_select_ckpt256_4096.json, configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: public frozen-source diagnostic after M549 route-health pass
- derived_from: m549-update-aligned-l3-route-pilot
- blocked_by: m549-update-aligned-l3-route-pilot
- supersedes: None
- invalidates: None

## Success Criteria

- all four public frozen-source surface evals complete
- aggregate and paired summaries compare selected M549 L3 against L0, L2, and original L3
- the result either admits matched repeat or classifies public-surface regression
- research validation passes

## Failure Criteria

- metadata or actor-contract validation fails
- eval uses different source surfaces from M543
- result is treated as private evidence or promotion

## Evidence Gates

- evaluate the M549 selected checkpoint on the same four public M543 frozen-source surfaces
- include M542 L0, M542 L2, original M542 L3, and M549 selected L3 in the same matrix
- compare paired deltas against L0/L2 and original L3
- do not promote checkpoint from public diagnostics alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not use private holdout or claim private generalization
- do not tune checkpoint selection from public frozen-source rows
- do not promote without matched multi-seed repeat

## Failure Taxonomy

- behavior_regression

## Scoreboard

- milestone: m550-m549-public-surface-diagnostic
- type: gate
- checkpoint: runs/m549_l3_repair_fast_select_ckpt256_seed3540/checkpoints/checkpoint_step_2816.pt
- success_rate: 0.724599
- termination_rate: None
- clearance_margin_mean: 1.148824
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_surface_regression_reject_repair_admit_m551_route_health_redesign
- reason: M550 selected L3 improves over original L3 but remains below L0 and L2 on all public surfaces

## Next Blocker

m551-route-health-screen-redesign
