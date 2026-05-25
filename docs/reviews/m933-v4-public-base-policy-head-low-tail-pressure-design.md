# m933-v4-public-base-policy-head-low-tail-pressure-design Research Review

## Summary

- Generated at UTC: 20260525T224210Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: policy_head_low_tail_pressure_design_admit_m934
- Decision reason: M933 designs stronger actor_mean-only low-tail pressure with target-active-set diagnostics before broadening feature or recurrent encoders

## Hypothesis

Because M932 shows actor_mean-only raw movement is normal-safe and weakly improves low-tail metrics, the next controlled step is stronger low-tail pressure with target-active-set diagnostics before broadening the trainable surface.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m932_v4_public_base_policy_head_raw_direction_feasibility/summary.json, runs/m932_v4_public_base_policy_head_raw_direction_feasibility/alpha_metrics.csv, docs/m932-v4-public-base-policy-head-raw-direction-feasibility-audit.md
- parent_config: experiments/manifests/m932-v4-public-base-policy-head-raw-direction-feasibility-audit.json
- parent_objective: design a stronger actor_mean-only low-tail pressure objective after M932 weak normal-safe movement
- derived_from: m932-v4-public-base-policy-head-raw-direction-feasibility-audit
- blocked_by: actor_mean-only low-tail pressure design has not yet been written
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m933-v4-public-base-policy-head-low-tail-pressure-design.md exists
- M933 keeps trainable surface actor_mean-only
- M933 pre-registers low-tail effect-size and target-active-set diagnostics
- M933 blocks replay PPO and promotion

## Failure Criteria

- M933 starts training
- M933 changes actor inputs
- M933 broadens trainable surface
- M933 admits replay PPO or promotion

## Evidence Gates

- M933 must be design-only
- M933 must preserve P0 actor input contract
- M933 must keep trainable surface at actor_mean only
- M933 must pre-register target-active-set diagnostics
- M933 must block replay PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M933
- do not change actor inputs
- do not broaden trainable surface in M933
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m933-v4-public-base-policy-head-low-tail-pressure-design
- type: infrastructure
- checkpoint: docs/m933-v4-public-base-policy-head-low-tail-pressure-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: policy_head_low_tail_pressure_design_admit_m934
- reason: M933 designs stronger actor_mean-only low-tail pressure with target-active-set diagnostics before broadening feature or recurrent encoders

## Next Blocker

actor_mean-only low-tail pressure design has not yet been written
