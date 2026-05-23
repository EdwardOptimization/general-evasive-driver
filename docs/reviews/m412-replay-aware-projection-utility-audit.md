# m412-replay-aware-projection-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T162754Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_m411_promotion_admit_m413_replay_recovery_balance_design
- Decision reason: M412 classifies M411 as retention-heavy: it keeps only 5.8 percent of M406 recovery improvement while reducing replay-anchor MSE to 0.03 percent of M406

## Hypothesis

The M411 proof-passing lambda 1e13 projection may be retention-heavy, so utility must be audited before any full public gate or chained repair.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt
- parent_dataset: runs/m411_combined_replay_failure_trajectory_anchor/combined_replay_failure_trajectory_anchor.npz, runs/m411_ltraj1e13_m267_m264_first_replay/summary.json, runs/m411_ltraj1e13_old_key_replay_gate/summary.json, runs/m411_ltraj1e13_m183_m170_first_replay/summary.json
- parent_config: experiments/manifests/m411-combined-replay-aware-projection-probe.json
- parent_objective: replay-aware exact projection with strong trajectory-anchor residual
- derived_from: m411-combined-replay-aware-projection-probe
- blocked_by: m411-combined-replay-aware-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- quantify parameter and action movement from M400 base
- quantify recovery-target movement retained versus M406 and M400
- compare exact-objective improvement against replay-trajectory collapse
- make an explicit decision: full public gate, redesign residual balance, or classify as retention-only

## Failure Criteria

- candidate movement cannot be measured
- audit tries to promote without full public gate
- audit uses private holdout feedback
- actor input or output contract changes

## Evidence Gates

- no PPO run
- no checkpoint promotion
- measure M411 movement from M400 base
- measure retained recovery-target movement versus M406
- classify as useful chained candidate or retention-only proof projection

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not count base-collapse as driver improvement

## Failure Taxonomy

- objective_overfit

## Scoreboard

- milestone: m412-replay-aware-projection-utility-audit
- type: gate
- checkpoint: runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m411_promotion_admit_m413_replay_recovery_balance_design
- reason: M412 classifies M411 as retention-heavy: it keeps only 5.8 percent of M406 recovery improvement while reducing replay-anchor MSE to 0.03 percent of M406

## Next Blocker

m413-replay-recovery-balance-design
