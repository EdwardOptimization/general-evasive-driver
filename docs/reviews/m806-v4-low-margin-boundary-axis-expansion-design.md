# m806-v4-low-margin-boundary-axis-expansion-design Research Review

## Summary

- Generated at UTC: 20260525T061908Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: boundary_axis_expansion_design_admit_m807
- Decision reason: M806 designs source-diverse boundary-axis expansion with lateral source-step fault-axis and bracketed retargeting plus axis-balance gates

## Hypothesis

A source-diverse boundary-axis expansion design can address M804's geometry-only and dominance failures without weakening the primary low-margin gate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m805-v4-low-margin-boundary-window-retarget-audit.md, docs/m804-v4-low-margin-boundary-window-retarget-implementation.md, runs/m804_v4_low_margin_boundary_window_retarget/summary.json, runs/m804_v4_low_margin_boundary_window_retarget/accepted_low_margin_window_rows.csv, runs/m804_v4_low_margin_boundary_window_retarget/diagnostic_axis_summary.csv, runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv
- parent_config: experiments/manifests/m805-v4-low-margin-boundary-window-retarget-audit.json
- parent_objective: design source-diverse boundary-axis expansion after M804 geometry-only diagnostic
- derived_from: m805-v4-low-margin-boundary-window-retarget-audit
- blocked_by: m804-v4-low-margin-boundary-window-retarget-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M806 documents an axis expansion design
- M806 specifies lateral, source-step, fault-activation, fault-severity, and distance-bisection retarget axes
- M806 specifies source-diversity, axis-diversity, and closed-loop replay acceptance gates
- M806 keeps the primary low-margin threshold unchanged
- M806 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- design only repeats obstacle half-width retargeting
- design weakens source-diversity or primary margin thresholds
- design uses oracle deploy-time inputs
- design admits training, PPO, or promotion
- design ignores workflow synthesis risk

## Evidence Gates

- M806 designs only; it does not implement or run a new retarget wave
- M806 preserves the P0 human-view actor contract
- M806 keeps alpha 0.2 and the primary <=0.00005 margin threshold unchanged
- M806 adds axis-diversity and source-diversity requirements
- M806 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not implement the axis expansion tool
- do not run another retarget wave
- do not train any parameters
- do not run PPO
- do not promote a checkpoint
- do not weaken seed or fault-pair dominance thresholds
- do not treat M804 geometry-only rows as source-diverse pass
- do not use private holdout feedback for public retargeting

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact
- objective_overfit

## Scoreboard

- milestone: m806-v4-low-margin-boundary-axis-expansion-design
- type: infrastructure
- checkpoint: docs/m806-v4-low-margin-boundary-axis-expansion-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: boundary_axis_expansion_design_admit_m807
- reason: M806 designs source-diverse boundary-axis expansion with lateral source-step fault-axis and bracketed retargeting plus axis-balance gates

## Next Blocker

m807-v4-low-margin-boundary-axis-expansion-implementation
