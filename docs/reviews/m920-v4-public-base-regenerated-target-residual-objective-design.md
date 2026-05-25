# m920-v4-public-base-regenerated-target-residual-objective-design Research Review

## Summary

- Generated at UTC: 20260525T214931Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_regenerated_target_residual_objective_design_admit_m921
- Decision reason: M920 designs frozen-M399 regenerated-target residual-head objective with normal-retention low-tail and target-MSE gates before exact compatibility replay PPO or promotion

## Hypothesis

M919 regenerated targets justify a frozen-M399 residual-head objective probe, but only after pre-registering normal-retention and low-tail candidate gates.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m919-v4-public-base-expanded-target-regeneration-implementation.md, runs/m919_v4_public_base_expanded_target_regeneration/summary.json, runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv, runs/m912_v4_public_base_sequence_recalibration_audit/summary.json, runs/m912_v4_public_base_sequence_recalibration_audit/low_tail_rows.csv, runs/m909_v4_public_base_residual_head_probe/objective_rows.csv
- parent_config: experiments/manifests/m919-v4-public-base-expanded-target-regeneration-implementation.json
- parent_objective: design frozen-M399 residual-head objective using regenerated M919 targets
- derived_from: m919-v4-public-base-expanded-target-regeneration-implementation
- blocked_by: M919 passed expanded target generation, but regenerated target residual objective is not yet designed
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m920-v4-public-base-regenerated-target-residual-objective-design.md exists
- M920 pre-registers regenerated target action loss and full-corpus normal retention
- M920 pre-registers candidate alpha gates before M921 training
- M920 keeps exact compatibility replay PPO and promotion blocked

## Failure Criteria

- M920 starts residual training
- M920 admits exact compatibility before objective metrics
- M920 changes actor inputs
- M920 starts replay PPO or promotion

## Evidence Gates

- M920 must be design-only
- M920 must train only a residual head in the future M921 design
- M920 must keep M880 exact compatibility, replay, PPO, and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M920
- do not update actor parameters
- do not run M880 exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m920-v4-public-base-regenerated-target-residual-objective-design
- type: infrastructure
- checkpoint: docs/m920-v4-public-base-regenerated-target-residual-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_regenerated_target_residual_objective_design_admit_m921
- reason: M920 designs frozen-M399 regenerated-target residual-head objective with normal-retention low-tail and target-MSE gates before exact compatibility replay PPO or promotion

## Next Blocker

m921-v4-public-base-regenerated-target-residual-probe-implementation
