# m791-v4-residual-component-sensitivity-design Research Review

## Summary

- Generated at UTC: 20260525T032009Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: residual_component_sensitivity_design_admit_m792
- Decision reason: M791 designs fixed steer throttle brake residual masks and alpha ladder 0.0 0.125 0.15 0.2 to attribute active-source normal collision risk and intervention lift before another vector objective

## Hypothesis

A no-training residual component sensitivity design can identify which M761 residual action dimensions are responsible for intervention lift and active-source normal collision risk.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m790-v4-vector-residual-calibration-audit.md, docs/m789-v4-vector-residual-calibration-implementation.md, runs/m789_v4_vector_residual_calibration/summary.json, runs/m789_v4_vector_residual_calibration/alpha_metrics.csv, runs/m789_v4_vector_residual_calibration/objective_rows.csv, runs/m789_v4_vector_residual_calibration/replay_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m790-v4-vector-residual-calibration-audit.json, experiments/manifests/m789-v4-vector-residual-calibration-implementation.json
- parent_objective: design a no-training residual component sensitivity probe after vector gate component collapse
- derived_from: m790-v4-vector-residual-calibration-audit
- blocked_by: m790-v4-vector-residual-calibration-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M791 documents component masks and alpha ladder
- M791 documents active-source and aggregate metrics
- M791 documents how to compare each component mask against M780 M786 and M789
- M791 keeps training PPO and promotion blocked

## Failure Criteria

- design trains parameters
- design changes actor input contract
- design weakens strict normal retention or gap thresholds
- design omits active-source analysis
- design admits PPO or promotion

## Evidence Gates

- M791 designs an audit-only residual component sensitivity probe
- M791 uses frozen M568 actor and frozen M761 residual head
- M791 defines component masks for steer throttle brake and combinations
- M791 defines active-source and intervention-gap metrics
- M791 blocks training PPO and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not implement the probe
- do not train actor residual or calibrator parameters
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken strict normal retention or gap metrics
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m791-v4-residual-component-sensitivity-design
- type: infrastructure
- checkpoint: docs/m791-v4-residual-component-sensitivity-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: residual_component_sensitivity_design_admit_m792
- reason: M791 designs fixed steer throttle brake residual masks and alpha ladder 0.0 0.125 0.15 0.2 to attribute active-source normal collision risk and intervention lift before another vector objective

## Next Blocker

m792-v4-residual-component-sensitivity-implementation
