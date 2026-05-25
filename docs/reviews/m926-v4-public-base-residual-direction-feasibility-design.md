# m926-v4-public-base-residual-direction-feasibility-design Research Review

## Summary

- Generated at UTC: 20260525T221107Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_residual_direction_feasibility_design_admit_m927
- Decision reason: M926 designs no-training alpha and direction-mixture feasibility sweep over M921 and M924 residual heads before any more residual training exact replay PPO or promotion

## Hypothesis

Before another residual training variant, a no-training feasibility audit should determine whether existing residual directions can satisfy both normal-retention and low-tail gates through alpha or direction mixing.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m925-v4-public-base-target-regeneration-branch-synthesis.md, runs/m921_v4_public_base_regenerated_target_residual_probe/summary.json, runs/m921_v4_public_base_regenerated_target_residual_probe/residual_head.pt, runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/summary.json, runs/m924_v4_public_base_alpha_aware_low_tail_residual_probe/residual_head.pt
- parent_config: experiments/manifests/m925-v4-public-base-target-regeneration-branch-synthesis.json
- parent_objective: design no-training feasibility audit over existing public-base residual directions
- derived_from: m925-v4-public-base-target-regeneration-branch-synthesis
- blocked_by: trust-region feasibility branch has not yet been designed
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m926-v4-public-base-residual-direction-feasibility-design.md exists
- M926 pre-registers no-training residual direction interpolation and alpha sweep
- M926 preserves exact compatibility replay PPO and promotion blocks

## Failure Criteria

- M926 starts training
- M926 omits normal-retention or low-tail gates
- M926 changes actor inputs or actor backbone
- M926 starts exact compatibility replay PPO or promotion

## Evidence Gates

- M926 must be design-only
- M926 must use existing residual heads only for no-training feasibility
- M926 must preserve frozen M399 and actor-input constraints
- M926 must block exact compatibility, replay, PPO, and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M926
- do not update actor parameters
- do not run exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m926-v4-public-base-residual-direction-feasibility-design
- type: infrastructure
- checkpoint: docs/m926-v4-public-base-residual-direction-feasibility-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_residual_direction_feasibility_design_admit_m927
- reason: M926 designs no-training alpha and direction-mixture feasibility sweep over M921 and M924 residual heads before any more residual training exact replay PPO or promotion

## Next Blocker

residual direction feasibility design has not yet been written
