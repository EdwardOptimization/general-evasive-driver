# m783-v4-normal-margin-aware-residual-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260525T023812Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_normal_margin_calibration_no_gap_lift
- Decision reason: M783 fixes active normal collisions with a frozen-actor frozen-residual calibrator but learns near-global half-gate behavior and fails intervention gap candidate threshold; no PPO or promotion

## Hypothesis

A small calibrator around the frozen M761 residual head can reduce residual action on low-margin normal branches while preserving intervention-sensitive residual separation.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m782-v4-normal-margin-aware-residual-calibration-design.md, docs/m781-v4-broader-normal-boundary-alpha-probe-audit.md, runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/objective_rows.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m782-v4-normal-margin-aware-residual-calibration-design.json
- parent_objective: implement no-PPO normal-margin-aware residual calibrator around frozen M761 residual head
- derived_from: m782-v4-normal-margin-aware-residual-calibration-design
- blocked_by: m782-v4-normal-margin-aware-residual-calibration-design
- supersedes: None
- invalidates: None

## Success Criteria

- M783 writes calibrator tooling and run artifacts
- M783 confirms actor and residual head checksums unchanged
- M783 trains only calibrator parameters
- M783 evaluates registered alphas 0.0 0.125 0.15 0.2
- M783 reports whether calibrated alpha 0.2 or 0.125 passes strict normal retention and gap gates

## Failure Criteria

- implementation mutates base actor or residual head
- implementation runs PPO
- implementation promotes a checkpoint
- implementation uses oracle labels as deploy-time inputs
- implementation omits active boundary source metrics

## Evidence Gates

- M783 implements normal-margin-aware calibrator tooling
- M783 freezes base actor and M761 residual head
- M783 trains only calibrator parameters
- M783 evaluates alpha 0.0 0.125 0.15 0.2
- M783 reports active source margin and intervention gap metrics
- M783 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not mutate base actor
- do not mutate M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not use terminal margin or fault labels as deploy-time inputs
- do not hide calibrator collapse
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m783-v4-normal-margin-aware-residual-calibration-implementation
- type: infrastructure
- checkpoint: runs/m783_v4_normal_margin_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_normal_margin_calibration_no_gap_lift
- reason: M783 fixes active normal collisions with a frozen-actor frozen-residual calibrator but learns near-global half-gate behavior and fails intervention gap candidate threshold; no PPO or promotion

## Next Blocker

m784-v4-normal-margin-aware-residual-calibration-audit
