# m942-v4-public-base-controlled-fusion-micro-boundary-audit Research Review

## Summary

- Generated at UTC: 20260525T232933Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: public_base_controlled_fusion_raw_direction_feasibility_candidate_route_to_exact_compatibility_design
- Decision reason: M942 no-training micro-alpha audit finds exact objective-level strict candidates at alphas 0.0675 0.0700 and 0.0725 while keeping training replay PPO and promotion blocked

## Hypothesis

The M940 raw direction may contain a narrow alpha between 0.05 and 0.075 that satisfies both normal retention and tail lift.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m940_v4_public_base_controlled_fusion_boundary_objective/checkpoints/raw_boundary_objective_update.pt
- parent_dataset: docs/m941-v4-public-base-controlled-fusion-branch-synthesis.md, runs/m940_v4_public_base_controlled_fusion_boundary_objective/summary.json, runs/m940_v4_public_base_controlled_fusion_boundary_objective/alpha_metrics.csv
- parent_config: experiments/manifests/m941-v4-public-base-controlled-fusion-branch-synthesis.json
- parent_objective: no-training fine alpha audit of the M940 raw boundary-objective direction
- derived_from: m941-v4-public-base-controlled-fusion-branch-synthesis
- blocked_by: M940 alpha 0.05 is normal-retained but not tail-lift, while alpha 0.075 tail-lifts just outside normal retention
- supersedes: None
- invalidates: None

## Success Criteria

- summary.json exists
- training_started is false
- forbidden_parameter_changed_between_checkpoints is false
- sample_reconstruction_success_rate >= 0.98
- strict_candidate_count is reported
- replay_used ppo_used and promoted are false

## Failure Criteria

- M942 trains or updates a checkpoint
- actor input contract changes
- forbidden parameters differ between checkpoints
- M942 runs replay PPO or promotion

## Evidence Gates

- M942 must compare M399 base against the M940 raw checkpoint
- M942 must run no training
- M942 must report whether any micro-alpha is a strict candidate
- M942 must keep replay PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not change actor inputs
- do not update any checkpoint
- do not run replay
- do not run PPO
- do not promote a checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m942-v4-public-base-controlled-fusion-micro-boundary-audit
- type: infrastructure
- checkpoint: runs/m942_v4_public_base_controlled_fusion_micro_boundary_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: public_base_controlled_fusion_raw_direction_feasibility_candidate_route_to_exact_compatibility_design
- reason: M942 no-training micro-alpha audit finds exact objective-level strict candidates at alphas 0.0675 0.0700 and 0.0725 while keeping training replay PPO and promotion blocked

## Next Blocker

m943-v4-public-base-controlled-fusion-candidate-compatibility-design
