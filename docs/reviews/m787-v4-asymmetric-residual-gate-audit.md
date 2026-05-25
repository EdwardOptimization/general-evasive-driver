# m787-v4-asymmetric-residual-gate-audit Research Review

## Summary

- Generated at UTC: 20260525T025841Z
- Type: gate
- Gate tier: process
- Promotion decision: pivot_to_vector_residual_calibration_design
- Decision reason: M787 audits M786 alpha 0.15 as a limited diagnostic positive but finds it remains close to scalar alpha scaling and does not solve alpha 0.2 so next step is vector residual calibration design

## Hypothesis

M786 should be audited as a limited diagnostic positive: alpha 0.15 passes strict normal retention and gap gates, but alpha 0.2 still fails and the gate behavior remains only moderately asymmetric.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m786-v4-asymmetric-residual-gate-implementation.md, runs/m786_v4_asymmetric_residual_gate/summary.json, runs/m786_v4_asymmetric_residual_gate/alpha_metrics.csv, runs/m786_v4_asymmetric_residual_gate/training_metrics.csv, runs/m786_v4_asymmetric_residual_gate/objective_rows.csv, docs/m785-v4-asymmetric-residual-gate-design.md, docs/m784-v4-normal-margin-aware-residual-calibration-audit.md
- parent_config: experiments/manifests/m786-v4-asymmetric-residual-gate-implementation.json, experiments/manifests/m785-v4-asymmetric-residual-gate-design.json
- parent_objective: audit high-default asymmetric residual gate candidate before any further calibration PPO or promotion
- derived_from: m786-v4-asymmetric-residual-gate-implementation
- blocked_by: m786-v4-asymmetric-residual-gate-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M787 records alpha 0.15 candidate status
- M787 records alpha 0.2 active-source normal collision
- M787 compares M786 gate behavior against M783 and intended M785 high-default design
- M787 classifies residual risks without PPO or promotion
- M787 admits only one next blocker

## Failure Criteria

- audit promotes a checkpoint
- audit admits PPO
- audit ignores normal-boundary margin
- audit treats alpha 0.15 as robust promotion evidence
- audit hides M773 hard-negative and current-model/proxy caveats

## Evidence Gates

- M787 audits M786 alpha 0.15 candidate
- M787 separates diagnostic candidate status from PPO or promotion readiness
- M787 records alpha 0.2 active-source failure
- M787 classifies whether M786 escaped M783 global half-scaling enough to continue scalar gating
- PPO training and checkpoint promotion remain blocked

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not call alpha 0.15 robust without auditing its small active-source margin
- do not hide alpha 0.2 normal collision
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure
- objective_overfit

## Scoreboard

- milestone: m787-v4-asymmetric-residual-gate-audit
- type: gate
- checkpoint: docs/m787-v4-asymmetric-residual-gate-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: pivot_to_vector_residual_calibration_design
- reason: M787 audits M786 alpha 0.15 as a limited diagnostic positive but finds it remains close to scalar alpha scaling and does not solve alpha 0.2 so next step is vector residual calibration design

## Next Blocker

m788-v4-asymmetric-residual-gate-next-step
