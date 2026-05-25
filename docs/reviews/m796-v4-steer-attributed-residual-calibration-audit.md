# m796-v4-steer-attributed-residual-calibration-audit Research Review

## Summary

- Generated at UTC: 20260525T043320Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_active_steer_guard_design
- Decision reason: M796 audits M795 as a clean near-miss negative and admits one design milestone for lexicographic active/source-diverse low-margin steer guarding while PPO and promotion remain blocked

## Hypothesis

M795 can be classified from artifacts as either an actionable steer-attributed candidate or a clean negative requiring a different evidence axis.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m795-v4-steer-attributed-residual-calibration-implementation.md, runs/m795_v4_steer_attributed_residual_calibration/summary.json, runs/m795_v4_steer_attributed_residual_calibration/alpha_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/gate_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/component_gate_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/active_source_metrics.csv
- parent_config: experiments/manifests/m795-v4-steer-attributed-residual-calibration-implementation.json
- parent_objective: audit steer-attributed residual calibration diagnostic
- derived_from: m795-v4-steer-attributed-residual-calibration-implementation
- blocked_by: m795-v4-steer-attributed-residual-calibration-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M796 documents supported and falsified claims from M795
- M796 classifies the failure or candidate type
- M796 identifies the next blocker
- M796 keeps PPO and promotion blocked

## Failure Criteria

- audit reruns training or PPO
- audit promotes a checkpoint
- audit ignores active-source margin miss
- audit claims broad generalization from the public corpus

## Evidence Gates

- M796 audits M795 without replay rerun
- M796 classifies whether M795 is a candidate or clean negative
- M796 checks active-source margin and steer selectivity
- M796 chooses the next blocker or stops residual calibration
- M796 blocks PPO and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train any parameters
- do not run PPO
- do not promote a checkpoint
- do not weaken M786 or M780 thresholds after seeing M795
- do not claim broad generalization from public M773 rows
- do not ignore active-source margin miss or steer-collapse evidence

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m796-v4-steer-attributed-residual-calibration-audit
- type: gate
- checkpoint: docs/m796-v4-steer-attributed-residual-calibration-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_active_steer_guard_design
- reason: M796 audits M795 as a clean near-miss negative and admits one design milestone for lexicographic active/source-diverse low-margin steer guarding while PPO and promotion remain blocked

## Next Blocker

m797-v4-active-steer-guard-calibration-design
