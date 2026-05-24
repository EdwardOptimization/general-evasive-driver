# m543-m542-public-surface-eval Research Review

## Summary

- Generated at UTC: 20260524T035216Z
- Type: gate
- Gate tier: proof
- Promotion decision: m542_public_eval_l2_dominant_l3_regression_admit_m544_l3_recipe_failure_audit
- Decision reason: M543 public frozen-source eval confirms L2 dominates and L3 regresses below L0 on seed3540; no checkpoint is promoted

## Hypothesis

The M542 route-pilot checkpoints can be compared on the same public frozen-source natural surfaces; given M542 route metrics, L2 may remain stronger than L3 under paired public diagnostics.

## Lineage

- parent_checkpoint: runs/m542_matched_l0_variance_seed3540/checkpoint.pt, runs/m542_matched_l2_variance_seed3540/checkpoint.pt, runs/m542_matched_l3_variance_seed3540/checkpoint.pt
- parent_dataset: runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_short_reveal.csv, runs/m497_natural_belief_decision_window_outcome_gate/targeted_pairs_warmup_capability.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_near_threshold.csv, runs/m487_critical_window_tail_aligned_outcome_gate/targeted_pairs_late_high_energy.csv
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: evaluate M542 route-pilot checkpoints on public frozen-source natural surfaces
- derived_from: m542-matched-history-variance-route-pilot, m537-full-public-natural-surface-eval
- blocked_by: m542-matched-history-variance-route-pilot
- supersedes: None
- invalidates: None

## Success Criteria

- all four public natural surface splits run or failures are diagnosed
- all three checkpoint metadata validations pass
- all-row and paired L3-L0/L3-L2 metrics are documented
- no checkpoint promotion is performed
- research validation passes

## Failure Criteria

- any M542 checkpoint cannot be evaluated
- metadata differs from the declared history level
- public event rows are treated as private evidence
- checkpoint promotion is performed

## Evidence Gates

- ran M542 L0 L2 L3 checkpoints on the four public frozen-source natural surfaces
- reported all-row and paired deltas
- kept M526 event overlay public and separate
- did not promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune M542 checkpoints from the public eval
- do not promote a route-pilot checkpoint
- do not treat M537/M543 public rows as private holdout

## Failure Taxonomy

- training_instability

## Scoreboard

- milestone: m543-m542-public-surface-eval
- type: gate
- checkpoint: runs/m543_m542_public_surface_eval_aggregate/summary.json
- success_rate: 0.866310
- termination_rate: None
- clearance_margin_mean: 1.777833
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: m542_public_eval_l2_dominant_l3_regression_admit_m544_l3_recipe_failure_audit
- reason: M543 public frozen-source eval confirms L2 dominates and L3 regresses below L0 on seed3540; no checkpoint is promoted

## Next Blocker

m544-l3-variance-recipe-failure-audit
