# m414-source-weighted-replay-anchor-probe Research Review

## Summary

- Generated at UTC: 20260523T163515Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_source_weighted_probe_admit_m415_active_set_replay_hinge_design
- Decision reason: M414 improves recovery retention to 23 percent of M406 but fails proof gates: M267/M264 15/17 and old-key compact has 2 accepted regressions

## Hypothesis

Keeping M267/M264 replay pressure at effective 1e12 while increasing only old-key replay-failure rows to effective 1e13 can retain first proof gates with more recovery movement than global 1e13.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m409_m407_m267_replay_failure_trajectory_anchor/rejected_trajectory_anchor.npz, runs/m410_old_key_replay_failure_trajectory_anchor/old_key_replay_failure_trajectory_anchor.npz, runs/m412_replay_aware_projection_utility_audit/summary.json
- parent_config: experiments/manifests/m413-replay-recovery-balance-design.json
- parent_objective: source-weighted replay trajectory anchor to avoid global over-anchoring
- derived_from: m413-replay-recovery-balance-design
- blocked_by: m412-replay-aware-projection-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- weighted anchor artifact contains 669 M267/M264 rows and 290 old-key rows
- old-key anchor weights are multiplied by 10 while M267/M264 weights are unchanged
- candidate passes exact M297/M270/old-key no-regression
- candidate passes M267/M264, old-key compact, and M183/M170 first proof gates
- candidate retains at least 20% of M406 recovery improvement

## Failure Criteria

- weighted anchor cannot be loaded
- exact projection has positive exact regression
- proof gates fail
- recovery-retention ratio remains below 0.20
- actor input or output contract changes

## Evidence Gates

- exact M297 no-regression
- exact M270 no-regression
- old-key surrogate no-regression
- M267/M264 first replay
- old-key compact replay
- M183/M170 first replay if first gates pass
- recovery improvement retained vs M406 >= 0.20

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not count retention-heavy projection as driver progress

## Failure Taxonomy

- proof_washout
- protected_key_window_failure

## Scoreboard

- milestone: m414-source-weighted-replay-anchor-probe
- type: gate
- checkpoint: runs/m414_source_weighted_projection_ltraj1e12_s40_seed10145/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_source_weighted_probe_admit_m415_active_set_replay_hinge_design
- reason: M414 improves recovery retention to 23 percent of M406 but fails proof gates: M267/M264 15/17 and old-key compact has 2 accepted regressions

## Next Blocker

m415-active-set-replay-hinge-design
