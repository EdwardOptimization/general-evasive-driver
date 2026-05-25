# m794-v4-steer-attributed-residual-calibration-design Research Review

## Summary

- Generated at UTC: 20260525T041717Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: steer_attributed_calibration_design_admit_m795
- Decision reason: M794 designs no-PPO steer-attributed residual calibration with steer-specific normal-boundary suppression brake retention fixed throttle default and component-collapse gates before any implementation

## Hypothesis

A steer-attributed residual calibration design can use M792 evidence to protect low-normal-margin steering residual while preserving intervention separation.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m793-v4-residual-component-sensitivity-audit.md, docs/m792-v4-residual-component-sensitivity-implementation.md, runs/m792_v4_residual_component_sensitivity/summary.json, runs/m792_v4_residual_component_sensitivity/mask_alpha_metrics.csv, runs/m792_v4_residual_component_sensitivity/component_role_metrics.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m793-v4-residual-component-sensitivity-audit.json
- parent_objective: design a steer-attributed residual calibration branch after M792 component attribution
- derived_from: m793-v4-residual-component-sensitivity-audit
- blocked_by: m793-v4-residual-component-sensitivity-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M794 documents a steer-specific no-PPO calibration design
- M794 states how harmful steering residual is identified and suppressed
- M794 states how useful steering and brake residual signal is retained
- M794 preserves actor and residual-head input contracts
- M794 keeps training PPO and promotion blocked

## Failure Criteria

- design ignores M792 steer useful/harmful attribution
- design becomes another generic vector gate
- design uses oracle deploy-time inputs
- design weakens M786 or M780 thresholds
- design admits PPO or promotion

## Evidence Gates

- M794 designs only; it does not implement or train
- M794 preserves the P0 human-view actor contract
- M794 targets steer-specific normal-boundary attenuation
- M794 preserves M786 and M780 comparison thresholds
- M794 blocks PPO and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not implement the calibrator
- do not train any parameters
- do not run replay as a result claim
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken M786 or M780 thresholds
- do not claim broad generalization from public M773 rows

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m794-v4-steer-attributed-residual-calibration-design
- type: infrastructure
- checkpoint: docs/m794-v4-steer-attributed-residual-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: steer_attributed_calibration_design_admit_m795
- reason: M794 designs no-PPO steer-attributed residual calibration with steer-specific normal-boundary suppression brake retention fixed throttle default and component-collapse gates before any implementation

## Next Blocker

m795-v4-steer-attributed-residual-calibration-implementation
