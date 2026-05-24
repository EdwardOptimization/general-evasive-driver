# m565-bc-public-natural-surface-eval Research Review

## Summary

- Generated at UTC: 20260524T053954Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc_public_surface_eval_pass_admit_scaled_bc_repeat_design
- Decision reason: M565 public diagnostics show M563_BC matches L2 success/collision and repairs original M542 L3; no checkpoint promotion

## Hypothesis

Because M563_BC passed route-screen v2 and is L2-competitive on fresh route seed 17560, it may repair the public natural-surface L3 regression observed in M543.

## Lineage

- parent_checkpoint: runs/m563_l3_behavior_cloning_smoke/checkpoint.pt, runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv, runs/m564_bc_route_screen_v2_smoke/summary.json
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: public frozen-source natural-surface diagnostic after M564 route-screen pass
- derived_from: m564-bc-route-screen-v2-smoke
- blocked_by: m564-bc-route-screen-v2-smoke
- supersedes: None
- invalidates: None

## Success Criteria

- all four public natural-surface evals complete
- aggregate and paired summaries compare M563_BC against L0, L2, and original L3
- result admits a larger distillation corpus or matched repeat if M563_BC is not worse than L2 within tolerance
- research validation passes

## Failure Criteria

- metadata or actor-contract validation fails
- M563_BC regresses below L0 or original L3 on public surfaces
- public diagnostics are treated as private evidence or checkpoint promotion

## Evidence Gates

- evaluate M563_BC on the same four public frozen-source natural surfaces used by M543/M550
- include L0, L2, original M542 L3, and M563_BC in the same matrices
- report aggregate and paired deltas against L0, L2, and original L3
- do not promote checkpoint from public diagnostics alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not treat public frozen-source rows as private generalization
- do not tune the M563 checkpoint from these public rows
- do not promote without matched repeat and generalization gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m565-bc-public-natural-surface-eval
- type: gate
- checkpoint: runs/m565_bc_public_natural_surface_eval_aggregate/summary.json
- success_rate: 0.866310
- termination_rate: 0.133690
- clearance_margin_mean: 1.770749
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_public_surface_eval_pass_admit_scaled_bc_repeat_design
- reason: M565 public diagnostics show M563_BC matches L2 success/collision and repairs original M542 L3; no checkpoint promotion

## Next Blocker

m566-scaled-bc-repeat-design
