# m785-v4-asymmetric-residual-gate-design Research Review

## Summary

- Generated at UTC: 20260525T024326Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: asymmetric_gate_design_admit_m786
- Decision reason: M785 designs high-default asymmetric residual gate with low-margin normal suppression as exception stronger intervention retention and unchanged strict normal/gap thresholds

## Hypothesis

An asymmetric high-default residual gate objective can preserve intervention-sensitive residual signal better than M783's near-global half-gate while still protecting low-margin normal branches.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m784-v4-normal-margin-aware-residual-calibration-audit.md, docs/m783-v4-normal-margin-aware-residual-calibration-implementation.md, runs/m783_v4_normal_margin_calibration/summary.json, runs/m783_v4_normal_margin_calibration/alpha_metrics.csv, runs/m783_v4_normal_margin_calibration/training_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m784-v4-normal-margin-aware-residual-calibration-audit.json, experiments/manifests/m783-v4-normal-margin-aware-residual-calibration-implementation.json
- parent_objective: design asymmetric residual gate after M783 global half-gate no-gap-lift result
- derived_from: m784-v4-normal-margin-aware-residual-calibration-audit
- blocked_by: m784-v4-normal-margin-aware-residual-calibration-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M785 specifies high-default gate initialization and prior
- M785 specifies low-margin normal suppression as an exception
- M785 specifies stronger intervention gate or gap retention
- M785 preserves strict normal retention and original gap thresholds
- M785 blocks PPO training and promotion

## Failure Criteria

- design admits PPO or promotion
- design mutates base actor or residual head
- design weakens candidate thresholds after M783
- design relies on deploy-time oracle inputs
- design ignores active source diagnostics

## Evidence Gates

- M785 designs asymmetric residual gate objective
- M785 keeps base actor and M761 residual head frozen
- M785 makes high gate the default and low-margin normal suppression the exception
- M785 adds stronger intervention gate and gap retention
- M785 blocks PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train in M785
- do not mutate base actor
- do not mutate M761 residual head
- do not run PPO
- do not promote a checkpoint
- do not use terminal margin or fault labels as deploy-time inputs
- do not weaken the M783 gap threshold after the near miss
- do not claim broad generalization or true four-wheel physical fidelity

## Failure Taxonomy

- objective_overfit
- scenario_sampling_failure
- behavior_regression

## Scoreboard

- milestone: m785-v4-asymmetric-residual-gate-design
- type: infrastructure
- checkpoint: docs/m785-v4-asymmetric-residual-gate-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: asymmetric_gate_design_admit_m786
- reason: M785 designs high-default asymmetric residual gate with low-margin normal suppression as exception stronger intervention retention and unchanged strict normal/gap thresholds

## Next Blocker

m786-v4-asymmetric-residual-gate-implementation
