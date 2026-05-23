# m368-old-key-hard-row-feedback-implementation Research Review

## Summary

- Generated at UTC: 20260523T120147Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m369_hard_row_weighted_repair_probe
- Decision reason: M368 implements hard-row overlay branch weights exports a 40-row weighted old-key corpus with one hard row and verifies no-update exact repair smoke without actor input changes

## Hypothesis

A hard-row overlay and branch-weight arrays can make replay-discovered wrong-history sign crossings visible to the differentiable old-key repair surrogate while preserving actor-input contract and backward compatibility.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: docs/m367-old-key-hard-row-weighting-design.md, runs/m364_old_key_aware_repair_alpha02_old_key_replay_gate/old_key_replay_comparison_rows.csv
- parent_config: experiments/manifests/m367-old-key-hard-row-weighting-design.json
- parent_objective: implement hard-row feedback overlay and branch-weight arrays for old-key preference corpus
- derived_from: m367-old-key-hard-row-weighting-design
- blocked_by: m367-old-key-hard-row-weighting-design
- supersedes: None
- invalidates: None

## Success Criteria

- old-key preference corpus accepts optional hard-row overlay CSV
- corpus NPZ records hard_row wrong_branch_weight and preferred_branch_weight arrays
- exact repair old-key surrogate uses branch weights when available
- backward compatibility tests pass when hard-row arrays are absent
- research validation passes

## Failure Criteria

- hard-row overlay changes deployable actor inputs
- existing old-key corpus behavior changes when overlay is absent
- tests fail
- research validation fails

## Evidence Gates

- infrastructure implementation only; no PPO run
- hard-row overlay does not change actor inputs
- old-key corpus remains backward-compatible when overlay absent
- focused tests pass
- research validation passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint
- do not lower old-key replay thresholds
- do not add hidden vehicle parameters or oracle labels to actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m368-old-key-hard-row-feedback-implementation
- type: infrastructure
- checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m369_hard_row_weighted_repair_probe
- reason: M368 implements hard-row overlay branch weights exports a 40-row weighted old-key corpus with one hard row and verifies no-update exact repair smoke without actor input changes

## Next Blocker

m369-hard-row-weighted-repair-probe
