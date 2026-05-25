# m786-v4-asymmetric-residual-gate-implementation Research Review

## Summary

- Generated at UTC: 20260525T025529Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_normal_margin_calibration_candidate_limited_alpha_015
- Decision reason: M786 implements high-default asymmetric scalar gate with unchanged actor and residual checksums; alpha 0.15 passes strict normal retention and gap gate but alpha 0.2 still collides on source 77025/source_index 12 so PPO and promotion remain blocked

## Hypothesis

A high-default asymmetric gate can preserve more intervention residual signal than M783 while retaining strict normal safety on the active low-margin source.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m785-v4-asymmetric-residual-gate-design.md, docs/m784-v4-normal-margin-aware-residual-calibration-audit.md, runs/m783_v4_normal_margin_calibration/summary.json, runs/m783_v4_normal_margin_calibration/alpha_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m785-v4-asymmetric-residual-gate-design.json
- parent_objective: implement high-default asymmetric residual gate after M783 global half-gate failure
- derived_from: m785-v4-asymmetric-residual-gate-design
- blocked_by: m785-v4-asymmetric-residual-gate-design
- supersedes: None
- invalidates: None

## Success Criteria

- M786 writes run artifacts and docs
- M786 confirms actor and residual head checksums unchanged
- M786 trains only calibrator parameters
- M786 evaluates registered alphas 0.0 0.125 0.15 0.2
- M786 reports gate statistics and active-source margins
- M786 records whether any alpha passes original strict normal and gap gates

## Failure Criteria

- implementation mutates base actor or residual head
- implementation runs PPO
- implementation promotes a checkpoint
- implementation weakens M783 gap threshold
- implementation omits gate statistics or active source metrics

## Evidence Gates

- M786 implements high-default asymmetric residual gate objective
- M786 freezes base actor and M761 residual head
- M786 trains only gate/calibrator parameters
- M786 evaluates alpha 0.0 0.125 0.15 0.2
- M786 reports whether gate escaped global half-scaling
- M786 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not mutate base actor
- do not mutate M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not weaken gap thresholds
- do not use terminal margin or fault labels as deploy-time inputs
- do not hide public active-source pressure
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure
- behavior_regression

## Scoreboard

- milestone: m786-v4-asymmetric-residual-gate-implementation
- type: infrastructure
- checkpoint: runs/m786_v4_asymmetric_residual_gate/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_normal_margin_calibration_candidate_limited_alpha_015
- reason: M786 implements high-default asymmetric scalar gate with unchanged actor and residual checksums; alpha 0.15 passes strict normal retention and gap gate but alpha 0.2 still collides on source 77025/source_index 12 so PPO and promotion remain blocked

## Next Blocker

m787-v4-asymmetric-residual-gate-audit
