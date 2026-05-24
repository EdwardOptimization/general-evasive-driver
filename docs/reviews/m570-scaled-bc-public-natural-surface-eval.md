# m570-scaled-bc-public-natural-surface-eval Research Review

## Summary

- Generated at UTC: 20260524T060340Z
- Type: gate
- Gate tier: proof
- Promotion decision: scaled_bc_public_surface_pass_admit_fresh_route_generalization_design
- Decision reason: M570 public diagnostics show BC5660 matches L2 success/collision slightly improves mean margin and repairs original M542 L3; no checkpoint promotion

## Hypothesis

Because the scaled BC family passed route-screen v2 on fresh seed 18560, selected BC5660 should at least match the M563_BC public natural-surface repair and remain L2-competitive.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv, runs/m569_scaled_bc_route_screen_selection/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: public frozen-source natural-surface diagnostic after scaled BC route-screen pass
- derived_from: m569-scaled-bc-route-screen-selection
- blocked_by: m569-scaled-bc-route-screen-selection
- supersedes: None
- invalidates: None

## Success Criteria

- all four public natural-surface evals complete
- aggregate and paired summaries compare BC5660 against L0 L2 and original L3
- BC5660 is L2-competitive on success collision and margin
- research validation passes

## Failure Criteria

- metadata or actor-contract validation fails
- BC5660 regresses below L0 or original L3 on public surfaces
- public diagnostics are treated as private evidence or checkpoint promotion

## Evidence Gates

- evaluate selected BC5660 on the same four public frozen-source natural surfaces used by M543/M550/M565
- include L0 L2 original M542 L3 and BC5660 in the same matrices
- report aggregate and paired deltas against L0 L2 and original L3
- do not promote checkpoint from public diagnostics alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat public frozen-source rows as private generalization
- do not tune BC5660 from public-surface residuals
- do not promote without fresh generalization and matched-repeat gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m570-scaled-bc-public-natural-surface-eval
- type: gate
- checkpoint: runs/m570_scaled_bc_public_natural_surface_eval_aggregate/summary.json
- success_rate: 0.866310
- termination_rate: 0.133690
- clearance_margin_mean: 1.782199
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: scaled_bc_public_surface_pass_admit_fresh_route_generalization_design
- reason: M570 public diagnostics show BC5660 matches L2 success/collision slightly improves mean margin and repairs original M542 L3; no checkpoint promotion

## Next Blocker

m571-fresh-route-generalization-design
