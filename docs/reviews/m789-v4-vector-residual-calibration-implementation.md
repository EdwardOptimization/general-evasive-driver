# m789-v4-vector-residual-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260525T031530Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_vector_residual_calibration_component_collapse
- Decision reason: M789 implements vector residual calibration with unchanged actor and residual checksums but gets no candidate because gate components collapse to scalar-like values and alpha 0.2 still collides on source 77025/source_index 12

## Hypothesis

A per-action-dimension vector gate can preserve intervention residual components while suppressing risky low-margin normal components, improving the M786 scalar-gate Pareto point.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m788-v4-vector-residual-calibration-design.md, docs/m787-v4-asymmetric-residual-gate-audit.md, runs/m786_v4_asymmetric_residual_gate/summary.json, runs/m786_v4_asymmetric_residual_gate/alpha_metrics.csv, runs/m783_v4_normal_margin_calibration/alpha_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/alpha_metrics.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m788-v4-vector-residual-calibration-design.json
- parent_objective: implement a no-PPO per-action-dimension residual gate after scalar gate behaves too much like alpha scaling
- derived_from: m788-v4-vector-residual-calibration-design
- blocked_by: m788-v4-vector-residual-calibration-design
- supersedes: None
- invalidates: None

## Success Criteria

- M789 writes run artifacts and docs
- M789 confirms actor and residual head checksums unchanged
- M789 trains only vector calibrator parameters
- M789 evaluates registered alphas 0.0 0.125 0.15 0.2
- M789 reports component gate statistics and active-source margins
- M789 records whether any alpha beats the M786 alpha 0.15 Pareto point

## Failure Criteria

- implementation mutates base actor or residual head
- implementation runs PPO
- implementation promotes a checkpoint
- implementation weakens M788 thresholds
- implementation omits component gate statistics or active source metrics

## Evidence Gates

- M789 implements a vector residual calibrator
- M789 freezes base actor and M761 residual head
- M789 trains only vector calibrator parameters
- M789 evaluates alpha 0.0 0.125 0.15 0.2
- M789 reports component-level gate metrics
- M789 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not mutate base actor
- do not mutate M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not weaken strict normal retention or intervention gap thresholds
- do not use terminal margin or fault labels as deploy-time inputs
- do not hide public active-source pressure
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m789-v4-vector-residual-calibration-implementation
- type: infrastructure
- checkpoint: runs/m789_v4_vector_residual_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_vector_residual_calibration_component_collapse
- reason: M789 implements vector residual calibration with unchanged actor and residual checksums but gets no candidate because gate components collapse to scalar-like values and alpha 0.2 still collides on source 77025/source_index 12

## Next Blocker

m790-v4-vector-residual-calibration-audit
