# m913-v4-public-base-tail-weighted-objective-design Research Review

## Summary

- Generated at UTC: 20260525T211746Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_tail_weighted_objective_design_admit_m914
- Decision reason: M913 designs M399 residual-head-only tail-weighted objective with explicit p10 deficit low-tail fraction and normal-retention gates

## Hypothesis

A design-only milestone can specify a safe M399 tail-weighted residual objective that targets the broad M912 low-tail row set while keeping actor update, replay, PPO, and promotion blocked.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m912-v4-public-base-sequence-recalibration-audit-implementation.md, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/group_deficit_summary.csv, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
- parent_config: experiments/manifests/m912-v4-public-base-sequence-recalibration-audit-implementation.json
- parent_objective: design a public-base tail-weighted residual objective for M399 low-tail rows
- derived_from: m912-v4-public-base-sequence-recalibration-audit-implementation
- blocked_by: M912 routes public-base sequence recalibration to tail-weighted objective design
- supersedes: None
- invalidates: None

## Success Criteria

- M913 defines row weights from low-tail and deficit severity
- M913 defines normal-retention penalties and gates
- M913 defines p10 and deficit admission gates
- M913 defines next implementation scope as residual-head-only with frozen M399
- M913 blocks replay, PPO, actor update, and promotion

## Failure Criteria

- M913 omits low-tail weighting
- M913 optimizes mean gap only
- M913 admits replay or PPO before residual-head-only evidence
- M913 does not define exact candidate gates

## Evidence Gates

- M913 must design tail weighting over M912 low-tail rows
- M913 must preserve normal-retention safeguards
- M913 must keep M399 actor frozen in the next implementation
- M913 must define exact candidate admission gates
- M913 must block replay, PPO, actor update, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M913
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not optimize only mean gap while ignoring p10 and deficit

## Failure Taxonomy

- none

## Scoreboard

- milestone: m913-v4-public-base-tail-weighted-objective-design
- type: infrastructure
- checkpoint: docs/m913-v4-public-base-tail-weighted-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_tail_weighted_objective_design_admit_m914
- reason: M913 designs M399 residual-head-only tail-weighted objective with explicit p10 deficit low-tail fraction and normal-retention gates

## Next Blocker

Public-base tail-weighted objective has not yet been designed
