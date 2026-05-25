# m795-v4-steer-attributed-residual-calibration-implementation Research Review

## Summary

- Generated at UTC: 20260525T043033Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_steer_attributed_calibration_component_collapse
- Decision reason: M795 implements steer-attributed no-PPO calibration and finds a clean negative: alpha 0.2 removes collision and reaches gap reference but active margin is too thin and active steer normal/intervention gates collapse

## Hypothesis

A steer-attributed calibrator can protect active-source normal margin while preserving enough intervention gap to beat the M786 alpha 0.15 reference.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m794-v4-steer-attributed-residual-calibration-design.md, docs/m793-v4-residual-component-sensitivity-audit.md, runs/m792_v4_residual_component_sensitivity/summary.json, runs/m792_v4_residual_component_sensitivity/component_role_metrics.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m773_v4_broader_source_holdout_corpus_export/contrast_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m794-v4-steer-attributed-residual-calibration-design.json
- parent_objective: implement no-PPO steer-attributed residual calibration diagnostic
- derived_from: m794-v4-steer-attributed-residual-calibration-design
- blocked_by: m794-v4-steer-attributed-residual-calibration-design
- supersedes: None
- invalidates: None

## Success Criteria

- M795 writes run artifacts and docs
- M795 confirms actor and residual head checksums unchanged
- M795 trains only calibrator parameters
- M795 reports component gate metrics and active-source metrics
- M795 classifies the result with the M794 taxonomy

## Failure Criteria

- implementation trains actor or residual parameters
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits active-source or component metrics
- implementation weakens comparison thresholds

## Evidence Gates

- M795 implements steer-attributed calibration only
- M795 freezes base actor and M761 residual head
- M795 trains only the small steer/brake calibrator
- M795 evaluates alpha 0.0 0.125 0.15 0.2 with active-source metrics
- M795 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train the base actor
- do not train the M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken M786 or M780 thresholds
- do not hide component-collapse or active-source failures
- do not claim broad generalization from public M773 rows

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m795-v4-steer-attributed-residual-calibration-implementation
- type: infrastructure
- checkpoint: runs/m795_v4_steer_attributed_residual_calibration/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_steer_attributed_calibration_component_collapse
- reason: M795 implements steer-attributed no-PPO calibration and finds a clean negative: alpha 0.2 removes collision and reaches gap reference but active margin is too thin and active steer normal/intervention gates collapse

## Next Blocker

m796-v4-steer-attributed-residual-calibration-audit
