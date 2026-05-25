# m782-v4-normal-margin-aware-residual-calibration-design Research Review

## Summary

- Generated at UTC: 20260525T022334Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: normal_margin_calibration_design_admit_m783
- Decision reason: M782 designs a no-PPO residual calibrator gate around frozen M761 residual outputs with low-margin normal suppression and intervention signal retention while keeping base actor inputs and weights unchanged

## Hypothesis

A normal-margin-aware residual calibration objective can preserve the useful intervention-separation signal from M761/M780 while reducing dangerous residual action on low-margin normal branches.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m781-v4-broader-normal-boundary-alpha-probe-audit.md, docs/m780-v4-broader-normal-boundary-alpha-probe-implementation.md, runs/m780_v4_broader_normal_boundary_alpha_probe/summary.json, runs/m780_v4_broader_normal_boundary_alpha_probe/alpha_metrics.csv, runs/m780_v4_broader_normal_boundary_alpha_probe/replay_rows.csv, runs/m773_v4_broader_source_holdout_corpus_export/positive_sequence_outcomes.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m781-v4-broader-normal-boundary-alpha-probe-audit.json, experiments/manifests/m780-v4-broader-normal-boundary-alpha-probe-implementation.json
- parent_objective: design normal-margin-aware residual calibration after alpha 0.125 limited feasibility and tiny boundary margin
- derived_from: m781-v4-broader-normal-boundary-alpha-probe-audit
- blocked_by: m781-v4-broader-normal-boundary-alpha-probe-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M782 specifies normal-margin retention terms for low-margin normal rows
- M782 specifies intervention separation terms that preserve action-gap and margin-gap signal
- M782 keeps base actor inputs and weights unchanged
- M782 defines exact and closed-loop gates for a later implementation
- M782 blocks PPO and promotion

## Failure Criteria

- design admits PPO or promotion
- design mutates the base actor
- design omits seed 77025/source_index 12
- design relies on deploy-time oracle inputs
- design ignores hard-negative sparsity and current-model/proxy caveats

## Evidence Gates

- M782 designs a normal-margin-aware residual calibration objective
- M782 keeps alpha 0.125 as diagnostic reference not promotion
- M782 protects low-margin normal rows such as seed 77025/source_index 12
- M782 preserves intervention action-gap and margin-gap objectives
- M782 blocks actor mutation PPO and checkpoint promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train in M782
- do not mutate the base actor
- do not run PPO
- do not promote a checkpoint
- do not use deploy-time oracle inputs
- do not hide alpha 0.125 tiny-margin caveat
- do not claim true four-wheel or per-wheel fault fidelity

## Failure Taxonomy

- behavior_regression
- scenario_sampling_failure

## Scoreboard

- milestone: m782-v4-normal-margin-aware-residual-calibration-design
- type: infrastructure
- checkpoint: docs/m782-v4-normal-margin-aware-residual-calibration-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: normal_margin_calibration_design_admit_m783
- reason: M782 designs a no-PPO residual calibrator gate around frozen M761 residual outputs with low-margin normal suppression and intervention signal retention while keeping base actor inputs and weights unchanged

## Next Blocker

m783-v4-normal-margin-aware-residual-calibration-implementation
