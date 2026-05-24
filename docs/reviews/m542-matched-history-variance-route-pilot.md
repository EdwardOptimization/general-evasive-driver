# m542-matched-history-variance-route-pilot Research Review

## Summary

- Generated at UTC: 20260524T034710Z
- Type: gate
- Gate tier: proof
- Promotion decision: matched_variance_route_pilot_pass_l2_strong_admit_m543_public_surface_eval
- Decision reason: M542 runs seed3540 4096-step L0 L2 L3 route pilot; L2 route eval is strongest but no checkpoint is promoted

## Hypothesis

The matched 4096-step config family can run all three history levels on seed 3540 and produce valid metadata before multi-seed variance evaluation.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: docs/m541-matched-history-variance-config-family.md
- parent_config: configs/ppo_m541_matched_l0_variance_4096.json, configs/ppo_m541_matched_l2_variance_4096.json, configs/ppo_m541_matched_l3_variance_4096.json
- parent_objective: run one-seed 4096-step matched L0 L2 L3 variance route pilot
- derived_from: m541-matched-history-variance-config-family
- blocked_by: m541-matched-history-variance-config-family
- supersedes: None
- invalidates: None

## Success Criteria

- L0 L2 and L3 runs complete
- all checkpoints record expected history_baseline and P0 input_contract metadata
- training summaries and eval summaries are documented
- no checkpoint promotion is performed
- research validation passes

## Failure Criteria

- any level cannot run from the matched config
- metadata differs from the declared history level
- P0 input contract changes
- checkpoint promotion is performed

## Evidence Gates

- ran L0 L2 and L3 4096-step configs on seed 3540
- validated checkpoint metadata and P0 input contract
- reported route/eval metrics without ranking claim
- did not promote checkpoint

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not tune configs after seeing one level's pilot result
- do not compare levels until all three pilot runs complete
- do not claim private generalization from route metrics

## Failure Taxonomy

- none

## Scoreboard

- milestone: m542-matched-history-variance-route-pilot
- type: gate
- checkpoint: runs/m542_matched_l2_variance_seed3540/checkpoint.pt
- success_rate: 77.992665
- termination_rate: 0.2
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: matched_variance_route_pilot_pass_l2_strong_admit_m543_public_surface_eval
- reason: M542 runs seed3540 4096-step L0 L2 L3 route pilot; L2 route eval is strongest but no checkpoint is promoted

## Next Blocker

m543-m542-public-surface-eval
