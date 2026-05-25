# m763-v4-residual-closed-loop-replay-design Research Review

## Summary

- Generated at UTC: 20260525T001847Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: v4_residual_closed_loop_replay_design_admit_m764
- Decision reason: M763 designs no-PPO base versus residual alpha replay with normal retention intervention sensitivity stratification and promotion blocked

## Hypothesis

A no-PPO closed-loop replay evaluator can be designed to test whether M761 exact residual gains survive rollout without actor mutation or promotion.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: docs/m762-v4-sequence-objective-only-probe-audit.md, runs/m761_v4_sequence_objective_probe/summary.json, runs/m761_v4_sequence_objective_probe/alpha_metrics.csv, runs/m761_v4_sequence_objective_probe/objective_rows.csv, runs/m761_v4_sequence_objective_probe/residual_head.pt
- parent_config: experiments/manifests/m762-v4-sequence-objective-only-probe-audit.json, configs/extreme_fault_distribution_v4_scenarios.json
- parent_objective: design no-PPO closed-loop replay for M761 residual head
- derived_from: m762-v4-sequence-objective-only-probe-audit
- blocked_by: m762-v4-sequence-objective-only-probe-audit
- supersedes: None
- invalidates: None

## Success Criteria

- M763 defines replay inputs and alpha set
- M763 defines normal and intervention replay branches
- M763 defines closed-loop metrics and stratification
- M763 defines sentinel and hard-negative diagnostics
- M763 blocks PPO, training, and promotion

## Failure Criteria

- design admits training or PPO
- design lacks closed-loop outcome metrics
- design ignores normal-history retention
- design ignores variant/horizon/fault-family stratification
- design treats exact objective gains as closed-loop proof

## Evidence Gates

- M763 designs base-vs-residual closed-loop replay
- M763 keeps PPO and promotion blocked
- M763 requires variant horizon and fault-family stratification
- M763 reports closed-loop outcomes separately from exact objective metrics
- M763 preserves actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train residual or actor parameters
- do not run PPO
- do not promote a checkpoint
- do not tune alphas from replay and call it unbiased
- do not claim true four-wheel or single-wheel physics
- do not hide closed-loop regressions behind exact objective gains

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m763-v4-residual-closed-loop-replay-design
- type: infrastructure
- checkpoint: docs/m763-v4-residual-closed-loop-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: v4_residual_closed_loop_replay_design_admit_m764
- reason: M763 designs no-PPO base versus residual alpha replay with normal retention intervention sensitivity stratification and promotion blocked

## Next Blocker

m764-v4-residual-closed-loop-replay-implementation
