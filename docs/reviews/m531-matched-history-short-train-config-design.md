# m531-matched-history-short-train-config-design Research Review

## Summary

- Generated at UTC: 20260524T025506Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: admit_m532_matched_short_train_single_seed
- Decision reason: M531 adds machine-checkable L0 L2 and L3 short-train configs with shared budget seeds and task distribution while preserving P0

## Hypothesis

A matched short-train config family for L0, L2, and L3 can be pre-registered with shared budget, seeds, and evaluation surfaces before running any trained-baseline comparison.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m526_history_value_event_audit/summary.json, runs/m530_l0_current_observation_smoke_seed3530, runs/m530_l0_current_observation_smoke_seed3531
- parent_config: configs/ppo_m528_l0_current_observation_smoke.json, experiments/manifests/m530-l0-baseline-smoke-repeat.json
- parent_objective: matched L0/L2/L3 short-train config family
- derived_from: m530-l0-baseline-smoke-repeat, m529-matched-history-baseline-eval-ladder-design
- blocked_by: m530-l0-baseline-smoke-repeat
- supersedes: None
- invalidates: None

## Success Criteria

- configs or config templates exist for L0, L2, and L3 short-train runs
- all configs declare history_baseline_level and P0 actor contract
- shared seeds and budgets are documented
- the next executable milestone is a small matched short-train run

## Failure Criteria

- configs use different budgets without justification
- configs change actor inputs outside P0
- design treats M526 public diagnostics as unbiased holdout
- checkpoint promotion is performed

## Evidence Gates

- defined matched L0/L2/L3 short-train configs with shared budget and seeds
- preserved P0 no-wheel no-privileged actor contract
- defined evaluation order without claiming private holdout evidence
- no long training or checkpoint promotion performed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune one baseline separately
- do not add privileged inputs
- do not interpret smoke returns as evidence
- do not promote a baseline checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m531-matched-history-short-train-config-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m532_matched_short_train_single_seed
- reason: M531 adds machine-checkable L0 L2 and L3 short-train configs with shared budget seeds and task distribution while preserving P0

## Next Blocker

m532-matched-short-train-single-seed
