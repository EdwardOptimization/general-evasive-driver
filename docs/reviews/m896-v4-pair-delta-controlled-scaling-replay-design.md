# m896-v4-pair-delta-controlled-scaling-replay-design Research Review

## Summary

- Generated at UTC: 20260525T201529Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: controlled_scaling_replay_design_admit_m897
- Decision reason: M896 designs exact-first replay/proof evaluation for M886 and M891 raw candidates before any PPO promotion or raw-candidate claim

## Hypothesis

The raw objective-only candidates may provide a larger but still controlled movement budget; M896 should design exact-first replay/proof evaluation before any execution or stronger claim.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt, runs/m886_v4_enriched_pair_delta_objective_only_probe/checkpoints/raw_candidate.pt, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/checkpoints/raw_candidate.pt
- parent_dataset: docs/m895-v4-pair-delta-objective-effect-size-budget-audit.md, runs/m886_v4_enriched_pair_delta_objective_only_probe/candidate_metrics.csv, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/candidate_metrics.csv, runs/m886_v4_enriched_pair_delta_objective_only_probe/action_drift_metrics.csv, runs/m891_v4_enriched_pair_delta_objective_only_repeat_seed10887/action_drift_metrics.csv
- parent_config: experiments/manifests/m895-v4-pair-delta-objective-effect-size-budget-audit.json
- parent_objective: design a controlled exact-first replay/proof gate for larger existing objective-only candidates before any scaling, PPO, or promotion
- derived_from: m895-v4-pair-delta-objective-effect-size-budget-audit
- blocked_by: M895 found alpha_0.1 proof-safe but too small; raw candidates have larger exact-objective movement but no replay evidence
- supersedes: None
- invalidates: None

## Success Criteria

- M896 writes a design document for raw-candidate exact/replay/behavior gates
- M896 names both raw candidate checkpoints and M568 baseline
- M896 specifies gate order and thresholds
- M896 defines failure routing
- M896 keeps replay execution, PPO, and promotion blocked

## Failure Criteria

- M896 runs replay or training
- M896 admits PPO or promotion
- M896 treats exact metrics as replay proof
- M896 omits one of the two raw candidate seeds
- M896 omits failure routing

## Evidence Gates

- M896 must design exact-first evaluation for both raw candidates
- M896 must require first replay gates before full replay stack
- M896 must require behavior seeds only if replay passes
- M896 must define failure routing for raw-candidate proof washout
- M896 must keep PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run replay in M896
- do not train actor or residual parameters
- do not run PPO
- do not promote a checkpoint
- do not accept raw candidates solely from exact metrics
- do not change actor inputs or residual head

## Failure Taxonomy

- proof_washout
- behavior_regression
- objective_overfit
- metric_artifact
- contract_violation
- lineage_invalid

## Scoreboard

- milestone: m896-v4-pair-delta-controlled-scaling-replay-design
- type: infrastructure
- checkpoint: docs/m896-v4-pair-delta-controlled-scaling-replay-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: controlled_scaling_replay_design_admit_m897
- reason: M896 designs exact-first replay/proof evaluation for M886 and M891 raw candidates before any PPO promotion or raw-candidate claim

## Next Blocker

Raw candidate controlled scaling replay/proof gate has not yet been designed
