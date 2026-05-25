# m797-v4-active-steer-guard-calibration-design Research Review

## Summary

- Generated at UTC: 20260525T043607Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: active_steer_guard_design_admit_m798
- Decision reason: M797 designs no-PPO active steer guard calibration with source-diverse low-margin rows supervised separability projection and exact gates before any implementation

## Hypothesis

An active-steer guard design can turn M795's collision-free strong-gap near miss into a safer diagnostic candidate by enforcing low-margin steering safety before gap optimization.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m796-v4-steer-attributed-residual-calibration-audit.md, docs/m795-v4-steer-attributed-residual-calibration-implementation.md, runs/m795_v4_steer_attributed_residual_calibration/summary.json, runs/m795_v4_steer_attributed_residual_calibration/alpha_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/gate_metrics.csv, runs/m795_v4_steer_attributed_residual_calibration/component_gate_metrics.csv
- parent_config: experiments/manifests/m796-v4-steer-attributed-residual-calibration-audit.json
- parent_objective: design an active-steer guard calibration after M795 steer-selectivity collapse
- derived_from: m796-v4-steer-attributed-residual-calibration-audit
- blocked_by: m796-v4-steer-attributed-residual-calibration-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M797 documents a lexicographic active-steer guard design
- M797 specifies source-diverse low-margin row selection
- M797 specifies exact active-source and component-selectivity gates
- M797 preserves actor and residual-head input contracts
- M797 keeps PPO and promotion blocked

## Failure Criteria

- design ignores M795 active margin miss
- design only changes scalar coefficients without a stronger guard mechanism
- design uses oracle deploy-time inputs
- design tunes only one public active source
- design admits PPO or promotion

## Evidence Gates

- M797 designs only; it does not implement or train
- M797 preserves the P0 human-view actor contract
- M797 makes active/low-margin steer safety lexicographic before gap optimization
- M797 requires source-diverse low-margin rows
- M797 blocks PPO and promotion

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
- do not tune only the single public active source

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m797-v4-active-steer-guard-calibration-design
- type: infrastructure
- checkpoint: docs/m797-v4-active-steer-guard-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: active_steer_guard_design_admit_m798
- reason: M797 designs no-PPO active steer guard calibration with source-diverse low-margin rows supervised separability projection and exact gates before any implementation

## Next Blocker

m798-v4-active-steer-guard-calibration-implementation
