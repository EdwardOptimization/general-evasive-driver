# m923-v4-public-base-alpha-aware-low-tail-objective-design Research Review

## Summary

- Generated at UTC: 20260525T220009Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_alpha_aware_low_tail_objective_design_admit_m924
- Decision reason: M923 designs an alpha-aware low-tail residual objective focused on normal-retaining alphas 0.20 and 0.35 after M921 target imitation failed tail lift gates

## Hypothesis

An alpha-aware low-tail objective can improve the metrics that blocked M921 inside the normal-retention trust region better than target-action imitation alone.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m922-v4-public-base-regenerated-target-residual-probe-audit.md, runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json, runs/m921_v4_public_base_regenerated_target_residual_probe/alpha_metrics.csv, runs/m919_v4_public_base_expanded_target_regeneration/accepted_target_rows.csv
- parent_config: experiments/manifests/m922-v4-public-base-regenerated-target-residual-probe-audit.json
- parent_objective: design alpha-aware low-tail objective after M921 target-action objective no-candidate result
- derived_from: m922-v4-public-base-regenerated-target-residual-probe-audit
- blocked_by: alpha-aware low-tail objective is not yet designed
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m923-v4-public-base-alpha-aware-low-tail-objective-design.md exists
- M923 pre-registers alpha-aware low-tail objective terms
- M923 preserves frozen-M399 and actor-input constraints
- M923 blocks exact compatibility replay PPO and promotion

## Failure Criteria

- M923 starts training
- M923 omits low-tail objective terms
- M923 changes actor inputs or actor backbone
- M923 starts exact compatibility replay PPO or promotion

## Evidence Gates

- M923 must be design-only
- M923 must preserve frozen M399 actor backbone
- M923 must target normal-retaining alpha range and low-tail lift directly
- M923 must block exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M923
- do not update actor parameters
- do not run exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m923-v4-public-base-alpha-aware-low-tail-objective-design
- type: infrastructure
- checkpoint: docs/m923-v4-public-base-alpha-aware-low-tail-objective-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_alpha_aware_low_tail_objective_design_admit_m924
- reason: M923 designs an alpha-aware low-tail residual objective focused on normal-retaining alphas 0.20 and 0.35 after M921 target imitation failed tail lift gates

## Next Blocker

alpha-aware low-tail objective design has not yet been written
