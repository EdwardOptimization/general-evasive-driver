# m818-v4-adaptive-primary-residual-calibration-audit Research Review

## Summary

- Generated at UTC: 20260525T090206Z
- Type: gate
- Gate tier: process
- Promotion decision: admit_adaptive_primary_calibration_followup_design
- Decision reason: M818 audits M817 as harness-positive but not performance-improving: near-identity gating preserves source-heldout normal intervention and old-behavior gates while proving no meaningful adaptive calibration yet

## Hypothesis

M817 validates the source-heldout calibration harness but should not be interpreted as a performance-improving driver update.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m817_v4_adaptive_primary_residual_calibration/summary.json, runs/m817_v4_adaptive_primary_residual_calibration/gate_summary.csv, runs/m817_v4_adaptive_primary_residual_calibration/train_eval_rows.csv, runs/m817_v4_adaptive_primary_residual_calibration/holdout_eval_rows.csv, runs/m817_v4_adaptive_primary_residual_calibration/intervention_eval_rows.csv, docs/m817-v4-adaptive-primary-residual-calibration-implementation.md
- parent_config: experiments/manifests/m817-v4-adaptive-primary-residual-calibration-implementation.json
- parent_objective: audit conservative source-heldout residual calibrator candidate
- derived_from: m817-v4-adaptive-primary-residual-calibration-implementation
- blocked_by: m817 conservative calibrator candidate requires audit before stronger objective
- supersedes: None
- invalidates: None

## Success Criteria

- M818 documents M817 split normal intervention and drift metrics
- M818 records supported and falsified claims
- M818 preserves no-PPO and no-promotion blocks
- M818 names the next blocker explicitly

## Failure Criteria

- M818 treats M817 as driver promotion
- M818 starts training or PPO
- M818 ignores the near-identity nature of the candidate
- M818 weakens exact gates or threshold requirements

## Evidence Gates

- M818 must audit M817 before stronger calibration or PPO
- M818 must not promote a checkpoint
- M818 must distinguish retention candidate from performance improvement
- M818 must preserve actor and residual-head contract boundaries
- M818 must decide whether stronger calibration design, vector ablation, or holdout wave is next

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not treat near-identity calibrator as performance improvement
- do not widen the primary 0.00005 margin threshold
- do not claim true wheel-level faults from current proxy data
- do not tune from private holdout failures

## Failure Taxonomy

- objective_overfit
- metric_artifact
- behavior_regression

## Scoreboard

- milestone: m818-v4-adaptive-primary-residual-calibration-audit
- type: gate
- checkpoint: docs/m818-v4-adaptive-primary-residual-calibration-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_adaptive_primary_calibration_followup_design
- reason: M818 audits M817 as harness-positive but not performance-improving: near-identity gating preserves source-heldout normal intervention and old-behavior gates while proving no meaningful adaptive calibration yet

## Next Blocker

m819-v4-adaptive-primary-calibration-followup-design
