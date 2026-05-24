# m528-matched-history-baseline-plumbing Research Review

## Summary

- Generated at UTC: 20260524T024642Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: matched_history_baseline_plumbing_smoke_pass_admit_m529_eval_ladder
- Decision reason: M528 adds explicit history_baseline_level metadata validates P0 no-wheel no-privileged inputs and runs an L0 smoke without promotion

## Hypothesis

Matched history baseline plumbing can be introduced without changing the P0 actor contract, enabling smoke-scale baseline comparisons after M526 diagnostic evidence.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json
- parent_config: experiments/manifests/m527-matched-history-baseline-design.json
- parent_objective: matched history baseline plumbing
- derived_from: m527-matched-history-baseline-design
- blocked_by: m527-matched-history-baseline-design
- supersedes: None
- invalidates: None

## Success Criteria

- history baseline metadata or config path is implemented
- at least one baseline level has a smoke train/eval or diagnostic path
- artifacts record baseline level and input contract
- actor inputs remain unchanged
- no checkpoint is promoted

## Failure Criteria

- baseline plumbing changes actor inputs
- checkpoint loading or config validation breaks
- training path cannot run a smoke
- checkpoint promotion is performed

## Evidence Gates

- implemented configurable history_baseline_level metadata
- L0 current-observation smoke train/eval completed
- P0 no-wheel no-privileged actor input contract preserved
- no long training or checkpoint promotion performed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote checkpoint
- do not add privileged actor inputs
- do not run long training before smoke validation
- do not overclaim incomplete L1/L2 support

## Failure Taxonomy

- none

## Scoreboard

- milestone: m528-matched-history-baseline-plumbing
- type: infrastructure
- checkpoint: runs/m528_l0_current_observation_smoke/checkpoint.pt
- success_rate: None
- termination_rate: 1.0
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: matched_history_baseline_plumbing_smoke_pass_admit_m529_eval_ladder
- reason: M528 adds explicit history_baseline_level metadata validates P0 no-wheel no-privileged inputs and runs an L0 smoke without promotion

## Next Blocker

m529-matched-history-baseline-eval-ladder-design
