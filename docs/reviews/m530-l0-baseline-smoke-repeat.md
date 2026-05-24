# m530-l0-baseline-smoke-repeat Research Review

## Summary

- Generated at UTC: 20260524T024946Z
- Type: infrastructure
- Gate tier: process
- Promotion decision: l0_smoke_repeat_pass_admit_m531_matched_short_train_config_design
- Decision reason: M530 repeats L0 current-observation smoke on seeds 3530 and 3531 and confirms stable L0/P0 metadata without performance claims

## Hypothesis

The L0 current-observation baseline smoke route is repeatable across fresh seeds and consistently records matched-history metadata, making it safe to proceed toward matched L0/L2/L3 short-train comparisons.

## Lineage

- parent_checkpoint: runs/m528_l0_current_observation_smoke/checkpoint.pt
- parent_dataset: runs/m528_l0_current_observation_smoke
- parent_config: configs/ppo_m528_l0_current_observation_smoke.json, experiments/manifests/m529-matched-history-baseline-eval-ladder-design.json
- parent_objective: L0 baseline smoke repeat
- derived_from: m529-matched-history-baseline-eval-ladder-design, m528-matched-history-baseline-plumbing
- blocked_by: m529-matched-history-baseline-eval-ladder-design
- supersedes: None
- invalidates: None

## Success Criteria

- at least two fresh-seed L0 smoke runs complete
- each run writes L0_current_observation metadata in config and checkpoint
- tests and research validation pass
- no checkpoint is promoted

## Failure Criteria

- any smoke run fails due to config or checkpoint metadata plumbing
- history_baseline metadata differs from the P0 L0 contract
- the recipe is tuned after seeing smoke returns
- a checkpoint is promoted

## Evidence Gates

- repeated L0 current-observation smoke on fresh seeds
- verified history_baseline metadata stability
- preserved P0 no-wheel no-privileged input contract
- no performance claims or checkpoint promotion performed

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote checkpoint
- do not change actor inputs
- do not tune the L0 recipe from smoke results
- do not compare smoke returns as baseline evidence

## Failure Taxonomy

- none

## Scoreboard

- milestone: m530-l0-baseline-smoke-repeat
- type: infrastructure
- checkpoint: runs/m530_l0_current_observation_smoke_seed3531/checkpoint.pt
- success_rate: None
- termination_rate: 1.0
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: l0_smoke_repeat_pass_admit_m531_matched_short_train_config_design
- reason: M530 repeats L0 current-observation smoke on seeds 3530 and 3531 and confirms stable L0/P0 metadata without performance claims

## Next Blocker

m531-matched-history-short-train-config-design
