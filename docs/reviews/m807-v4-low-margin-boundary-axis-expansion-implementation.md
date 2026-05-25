# m807-v4-low-margin-boundary-axis-expansion-implementation Research Review

## Summary

- Generated at UTC: 20260525T064111Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
- Decision reason: M807 replays 7882 multi-axis candidates with unchanged checksums but all 252 primary-window accepted rows still come only from obstacle-half-width so source and axis diversity gates fail

## Hypothesis

Adding lateral, source-step, fault-axis, and bracketed retargeting can produce source-diverse and axis-diverse primary low-margin rows without weakening the gate.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m806-v4-low-margin-boundary-axis-expansion-design.md, docs/m805-v4-low-margin-boundary-window-retarget-audit.md, runs/m804_v4_low_margin_boundary_window_retarget/summary.json, runs/m804_v4_low_margin_boundary_window_retarget/retarget_replay_rows.csv, runs/m804_v4_low_margin_boundary_window_retarget/accepted_low_margin_window_rows.csv, runs/m801_v4_low_margin_source_diverse_reference_replay/replay_rows.csv
- parent_config: experiments/manifests/m806-v4-low-margin-boundary-axis-expansion-design.json, configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json
- parent_objective: implement no-training source-diverse boundary-axis expansion
- derived_from: m806-v4-low-margin-boundary-axis-expansion-design
- blocked_by: m804-v4-low-margin-boundary-window-retarget-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- M807 writes axis anchor, plan, replay, accepted, rejected, balance, bracket, progress, summary, and documentation artifacts
- M807 reports accepted rows, unique seeds, source indices, fault-family pairs, retarget axes, and dominance metrics
- M807 confirms actor and residual-head checksums unchanged
- M807 classifies the result without widening the primary margin gate
- M807 keeps residual calibration, PPO, and promotion blocked

## Failure Criteria

- implementation trains actor, residual head, or a new calibrator
- implementation runs PPO
- implementation promotes a checkpoint
- implementation omits source-diversity or axis-diversity diagnostics
- implementation treats M804 half-width rows as primary-pass evidence without axis diversity
- implementation changes margin by post-processing rather than closed-loop replay

## Evidence Gates

- M807 implements and runs only no-training axis expansion
- M807 preserves the P0 human-view actor contract
- M807 keeps alpha 0.2 and the primary <=0.00005 margin threshold unchanged
- M807 requires source-diversity and axis-diversity before pass
- M807 confirms actor and M761 residual-head checksums unchanged
- M807 blocks residual calibration, PPO, and promotion

## Holdout Policy

- promotion_only

## Forbidden Shortcuts

- do not train actor or residual parameters
- do not train a new residual calibrator
- do not run PPO
- do not promote a checkpoint
- do not add oracle deploy-time inputs
- do not widen the primary 0.00005 margin threshold
- do not weaken seed source or fault dominance thresholds
- do not treat M804 half-width rows alone as source-diverse pass
- do not post-process margins after rollout
- do not tune from private holdout failures

## Failure Taxonomy

- scenario_sampling_failure
- metric_artifact

## Scoreboard

- milestone: m807-v4-low-margin-boundary-axis-expansion-implementation
- type: infrastructure
- checkpoint: runs/m807_v4_low_margin_boundary_axis_expansion/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_low_margin_boundary_axis_expansion_geometry_only_diagnostic
- reason: M807 replays 7882 multi-axis candidates with unchanged checksums but all 252 primary-window accepted rows still come only from obstacle-half-width so source and axis diversity gates fail

## Next Blocker

m808-v4-low-margin-boundary-axis-expansion-audit
