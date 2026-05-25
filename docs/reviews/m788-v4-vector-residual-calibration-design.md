# m788-v4-vector-residual-calibration-design Research Review

## Summary

- Generated at UTC: 20260525T030139Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: vector_residual_calibration_design_admit_m789
- Decision reason: M788 designs a conservative no-PPO per-action-dimension residual gate with frozen M568 actor frozen M761 residual head alpha 0.2 primary target and explicit M780 M783 M786 comparison gates

## Hypothesis

A vector or structured residual calibration design can address M787's scalar-gate limitation by suppressing risky normal action components without globally shrinking useful intervention residuals.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m787-v4-asymmetric-residual-gate-audit.md, docs/m786-v4-asymmetric-residual-gate-implementation.md, runs/m786_v4_asymmetric_residual_gate/summary.json, runs/m786_v4_asymmetric_residual_gate/alpha_metrics.csv, runs/m783_v4_normal_margin_calibration/alpha_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/alpha_metrics.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m787-v4-asymmetric-residual-gate-audit.json, experiments/manifests/m786-v4-asymmetric-residual-gate-implementation.json
- parent_objective: design a more expressive residual calibration probe after scalar gate produces only a narrow alpha 0.15 diagnostic candidate
- derived_from: m787-v4-asymmetric-residual-gate-audit
- blocked_by: m787-v4-asymmetric-residual-gate-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M788 documents the vector residual calibration objective
- M788 documents deploy-time inputs and forbidden training-time-only signals
- M788 defines strict normal retention and intervention gap gates
- M788 defines comparison targets against M780 M783 and M786
- M788 keeps implementation PPO and promotion blocked

## Failure Criteria

- design changes the actor input contract
- design mutates base actor or residual head
- design weakens M786 thresholds
- design admits PPO or promotion
- design omits comparison against scalar-gate baselines

## Evidence Gates

- M788 designs a vector or structured residual calibration probe
- M788 preserves the M568 base actor and M761 residual head as frozen references
- M788 preserves the human-view deployable input contract
- M788 defines explicit comparison targets against M780 alpha 0.125 M783 alpha 0.2 and M786 alpha 0.15
- M788 blocks implementation PPO and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not implement the calibrator
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not weaken strict normal retention or intervention gap thresholds
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m788-v4-vector-residual-calibration-design
- type: infrastructure
- checkpoint: docs/m788-v4-vector-residual-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: vector_residual_calibration_design_admit_m789
- reason: M788 designs a conservative no-PPO per-action-dimension residual gate with frozen M568 actor frozen M761 residual head alpha 0.2 primary target and explicit M780 M783 M786 comparison gates

## Next Blocker

m789-v4-vector-residual-calibration-implementation
