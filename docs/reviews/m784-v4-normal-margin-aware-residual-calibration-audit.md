# m784-v4-normal-margin-aware-residual-calibration-audit Research Review

## Summary

- Generated at UTC: 20260525T024054Z
- Type: gate
- Gate tier: process
- Promotion decision: promote_to_asymmetric_residual_gate_design
- Decision reason: M784 audits M783 as clean no-gap-lift: normal retention is fixed but global half-gate under-shoots intervention gap; next is high-default asymmetric gate design with PPO and promotion blocked

## Hypothesis

M783 should be audited as a clean negative: normal-margin calibration fixed the active normal collision but behaved like global residual downscaling and failed the intervention-gap candidate gate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m783-v4-normal-margin-aware-residual-calibration-implementation.md, runs/m783_v4_normal_margin_calibration/summary.json, runs/m783_v4_normal_margin_calibration/alpha_metrics.csv, runs/m783_v4_normal_margin_calibration/training_metrics.csv, runs/m783_v4_normal_margin_calibration/objective_rows.csv, docs/m782-v4-normal-margin-aware-residual-calibration-design.md
- parent_config: experiments/manifests/m783-v4-normal-margin-aware-residual-calibration-implementation.json, experiments/manifests/m782-v4-normal-margin-aware-residual-calibration-design.json
- parent_objective: audit first normal-margin-aware residual calibration result before further repair PPO or promotion
- derived_from: m783-v4-normal-margin-aware-residual-calibration-implementation
- blocked_by: m783-v4-normal-margin-aware-residual-calibration-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M784 records normal retention pass
- M784 records candidate_alpha_count 0
- M784 records near-global half-gate behavior
- M784 classifies objective failure without PPO or promotion
- M784 admits only one next blocker

## Failure Criteria

- audit promotes a checkpoint
- audit admits PPO
- audit hides gap failure
- audit treats normal retention alone as candidate
- audit ignores source and hard-negative caveats

## Evidence Gates

- M784 audits M783 calibrator result
- M784 separates normal-retention fix from intervention-gap insufficiency
- M784 classifies global half-gate behavior
- M784 decides whether to redesign calibration objective or stop branch
- PPO training and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not call M783 a candidate despite normal retention pass
- do not hide intervention-gap failure
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure
- behavior_regression

## Scoreboard

- milestone: m784-v4-normal-margin-aware-residual-calibration-audit
- type: gate
- checkpoint: docs/m784-v4-normal-margin-aware-residual-calibration-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: promote_to_asymmetric_residual_gate_design
- reason: M784 audits M783 as clean no-gap-lift: normal retention is fixed but global half-gate under-shoots intervention gap; next is high-default asymmetric gate design with PPO and promotion blocked

## Next Blocker

m785-v4-asymmetric-residual-gate-design
