# m1546-paper-route-calibrated-terminal-boundary-history-intervention-design Research Review

## Summary

- Generated at UTC: 20260529T120836Z
- Type: gate
- Gate tier: process
- Promotion decision: calibrated_terminal_boundary_history_intervention_design_admit_bounded_implementation
- Decision reason: M1546 designs measured response/context pair construction and calibrated history/control interventions over M1544 near-boundary rows with materialization blocked

## Hypothesis

A calibrated terminal-boundary history-intervention design can test whether wrong-history or donor response/action history changes outcome on actual near-boundary rows while preserving controls and guardrails.

## Lineage

- parent_checkpoint: runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m1545-paper-route-terminal-boundary-task-sampling-calibration-result-audit.md, runs/m1544_terminal_boundary_task_sampling_calibration_smoke/summary.json, runs/m1544_terminal_boundary_task_sampling_calibration_smoke/accepted_calibrated_rows.csv
- parent_config: experiments/manifests/m1545-paper-route-terminal-boundary-task-sampling-calibration-result-audit.json
- parent_objective: design calibrated terminal-boundary history interventions over actual near-boundary rows
- derived_from: m1545-paper-route-terminal-boundary-task-sampling-calibration-result-audit
- blocked_by: history interventions have not yet been run on calibrated terminal-boundary rows
- supersedes: direct materialization of M1544 calibrated rows
- invalidates: None

## Success Criteria

- docs/m1546-paper-route-calibrated-terminal-boundary-history-intervention-design.md exists
- design defines calibrated measured trace reconstruction and pair gates
- design defines history interventions, controls, and terminal-positive thresholds
- candidate materialization training PPO promotion private holdout actor-input changes and training-corpus export remain blocked
- follow-up implementation manifest exists

## Failure Criteria

- design document is missing
- design treats M1544 calibration as history-necessity evidence
- design skips matched scene/current-state pair construction
- design routes directly to training promotion private holdout or materialization

## Evidence Gates

- M1546 must design calibrated measured traces before interventions
- M1546 must preserve P0 actor input contract
- M1546 must separate history interventions from reset/zero-current controls
- M1546 must keep materialization and training blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote
- do not use private holdout
- do not add actor inputs
- do not export training corpus
- do not materialize candidates
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1546-paper-route-calibrated-terminal-boundary-history-intervention-design
- type: gate
- checkpoint: docs/m1546-paper-route-calibrated-terminal-boundary-history-intervention-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: calibrated_terminal_boundary_history_intervention_design_admit_bounded_implementation
- reason: M1546 designs measured response/context pair construction and calibrated history/control interventions over M1544 near-boundary rows with materialization blocked

## Next Blocker

m1547-paper-route-calibrated-terminal-boundary-history-intervention-implementation
