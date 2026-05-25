# m936-v4-public-base-controlled-fusion-surface-design Research Review

## Summary

- Generated at UTC: 20260525T225249Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: controlled_fusion_surface_design_admit_m937
- Decision reason: M936 designs actor_mean plus response_context_fusion.0 trainable surface with response context encoders GRU critic log_std replay PPO and promotion blocked

## Hypothesis

A narrowly controlled fusion-plus-head trainable surface is the next reasonable step after actor_mean-only trust-region conflict, while keeping recurrent and perception encoders frozen.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m935-v4-public-base-policy-level-trust-region-branch-synthesis.md, runs/m934_v4_public_base_policy_head_low_tail_pressure/summary.json
- parent_config: experiments/manifests/m935-v4-public-base-policy-level-trust-region-branch-synthesis.json
- parent_objective: design a controlled broader trainable surface after actor_mean-only branch synthesis
- derived_from: m935-v4-public-base-policy-level-trust-region-branch-synthesis
- blocked_by: controlled fusion surface design has not yet been written
- supersedes: None
- invalidates: None

## Success Criteria

- docs/m936-v4-public-base-controlled-fusion-surface-design.md exists
- M936 lists allowed and forbidden trainable parameter groups
- M936 pre-registers checksums and objective diagnostics
- M936 blocks exact compatibility replay PPO and promotion

## Failure Criteria

- M936 starts training
- M936 changes actor inputs
- M936 omits trainable-surface checksums
- M936 admits replay PPO or promotion

## Evidence Gates

- M936 must be design-only
- M936 must preserve P0 actor input contract
- M936 must specify allowed trainable parameters
- M936 must keep response/context encoders and GRU frozen unless explicitly justified
- M936 must block replay PPO and promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in M936
- do not change actor inputs
- do not run exact compatibility
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m936-v4-public-base-controlled-fusion-surface-design
- type: infrastructure
- checkpoint: docs/m936-v4-public-base-controlled-fusion-surface-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_fusion_surface_design_admit_m937
- reason: M936 designs actor_mean plus response_context_fusion.0 trainable surface with response context encoders GRU critic log_std replay PPO and promotion blocked

## Next Blocker

controlled fusion surface design has not yet been written
