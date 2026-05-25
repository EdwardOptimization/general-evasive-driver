# m932-v4-public-base-policy-head-raw-direction-feasibility-audit Research Review

## Summary

- Generated at UTC: 20260525T223901Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_policy_head_raw_direction_feasibility_no_tail_lift_route_to_low_tail_pressure_design
- Decision reason: M932 finds the M930 raw actor_mean direction is normal-safe and weakly improves low-tail metrics at alpha 1.0 but has zero tail-lift rows and no candidate

## Hypothesis

The M930 raw actor_mean direction may reveal whether actor-head-only updates have tail-lift leverage outside the conservative alpha window, without any new training.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m930_v4_public_base_policy_head_trust_region_probe/checkpoints/raw_actor_mean_update.pt
- parent_dataset: runs/m930_v4_public_base_policy_head_trust_region_probe/summary.json, runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, docs/m931-v4-public-base-policy-head-no-tail-lift-audit.md
- parent_config: experiments/manifests/m931-v4-public-base-policy-head-no-tail-lift-audit.json
- parent_objective: no-training extended-alpha feasibility audit of M930 raw actor_mean direction
- derived_from: m931-v4-public-base-policy-head-no-tail-lift-audit
- blocked_by: M930 raw actor-head direction has not been evaluated beyond the conservative alpha window
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- training_started is false
- base and raw checkpoints differ only in actor_mean
- sample_reconstruction_success_rate >= 0.98
- alpha grid includes values above 0.1
- route decision is recorded without replay PPO or promotion

## Failure Criteria

- M932 starts training
- base and raw checkpoints differ outside actor_mean
- actor input contract changes
- M932 runs replay PPO or promotion

## Evidence Gates

- M932 must be no-training
- M932 must compare base M399 to M930 raw actor_mean direction
- M932 must preserve P0 actor input contract
- M932 must block replay PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M932
- do not change actor inputs
- do not update checkpoints
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m932-v4-public-base-policy-head-raw-direction-feasibility-audit
- type: infrastructure
- checkpoint: runs/m932_v4_public_base_policy_head_raw_direction_feasibility/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_policy_head_raw_direction_feasibility_no_tail_lift_route_to_low_tail_pressure_design
- reason: M932 finds the M930 raw actor_mean direction is normal-safe and weakly improves low-tail metrics at alpha 1.0 but has zero tail-lift rows and no candidate

## Next Blocker

M930 raw actor-head direction has not been evaluated beyond the conservative alpha window
