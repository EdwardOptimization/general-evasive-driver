# m415-active-set-replay-hinge-design Research Review

## Summary

- Generated at UTC: 20260523T163911Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m416_active_set_hinge_anchor_implementation
- Decision reason: M415 designs radius-aware active-set hinge residual for M267 rows 6/15 and old-key active cases 10004/9998 with 10023 as guard

## Hypothesis

A row/branch active-set hinge residual can preserve replay proof while allowing recovery movement better than scalar replay-anchor MSE.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m414_source_weighted_projection_ltraj1e12_s40_seed10145/candidate_checkpoint.pt
- parent_dataset: runs/m414_source_weighted_utility_audit/summary.json, runs/m414_source_weighted_m267_m264_first_replay/summary.json, runs/m414_source_weighted_old_key_replay_gate/summary.json
- parent_config: experiments/manifests/m414-source-weighted-replay-anchor-probe.json
- parent_objective: design active-set replay hinge residual after source-weighted scalar tradeoff
- derived_from: m414-source-weighted-replay-anchor-probe
- blocked_by: m414-source-weighted-replay-anchor-probe
- supersedes: None
- invalidates: None

## Success Criteria

- define row-level active-set construction from M411/M414 replay failures
- define slack-radius action hinge residual for replay-safe rows
- define tight anchors only for rows or branches that are near replay failure
- define a no-PPO implementation/probe milestone with recovery-retention and proof gates

## Failure Criteria

- design weakens proof gates
- design uses replay labels as actor inputs
- design cannot be evaluated without PPO
- design lacks a utility acceptance rule

## Evidence Gates

- design only
- no PPO run
- no checkpoint promotion
- no actor input/output change

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not count utility improvement as sufficient without proof gates

## Failure Taxonomy

- none

## Scoreboard

- milestone: m415-active-set-replay-hinge-design
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m416_active_set_hinge_anchor_implementation
- reason: M415 designs radius-aware active-set hinge residual for M267 rows 6/15 and old-key active cases 10004/9998 with 10023 as guard

## Next Blocker

m416-active-set-hinge-anchor-implementation
