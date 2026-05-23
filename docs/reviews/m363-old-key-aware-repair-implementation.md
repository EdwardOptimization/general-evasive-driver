# m363-old-key-aware-repair-implementation Research Review

## Summary

- Generated at UTC: 20260523T113626Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m364_old_key_aware_repair_probe
- Decision reason: M363 implements old-key preference corpus and optional exact repair surrogate; exports 40-row corpus and verifies no-update repair smoke with old-key metrics

## Hypothesis

An optional old-key preference corpus and old-key surrogate loss can be added to exact post-PPO repair while preserving existing repair behavior when disabled.

## Lineage

- parent_checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- parent_dataset: docs/m362-old-key-aware-exact-repair-design.md, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m362-old-key-aware-exact-repair-design.json
- parent_objective: implement old-key-aware exact repair/projection without PPO
- derived_from: m362-old-key-aware-exact-repair-design
- blocked_by: m362-old-key-aware-exact-repair-design
- supersedes: None
- invalidates: None

## Success Criteria

- old-key preference corpus module exports and validates NPZ/metadata artifacts
- exact_post_ppo_repair accepts optional old-key corpus arguments
- selection trace records old-key surrogate metrics when enabled
- backward compatibility tests pass
- research validation passes

## Failure Criteria

- existing exact repair behavior changes when old-key corpus is omitted
- old-key corpus includes privileged actor inputs
- tests fail
- research validation fails

## Evidence Gates

- infrastructure implementation only; no PPO run
- old-key preference corpus validates without privileged actor inputs
- exact repair remains backward-compatible when old-key corpus is absent
- focused tests pass
- research validation passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not add hidden parameters or oracle labels to actor inputs
- do not replace closed-loop old-key replay gates with the surrogate

## Failure Taxonomy

- none

## Scoreboard

- milestone: m363-old-key-aware-repair-implementation
- type: infrastructure
- checkpoint: runs/m358_m352_to_m354_best_step_micro_interpolation/checkpoints/alpha_0_00025.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m364_old_key_aware_repair_probe
- reason: M363 implements old-key preference corpus and optional exact repair surrogate; exports 40-row corpus and verifies no-update repair smoke with old-key metrics

## Next Blocker

m364-old-key-aware-repair-probe
