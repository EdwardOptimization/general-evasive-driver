# m411-combined-replay-aware-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T162318Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m412_replay_aware_projection_utility_audit
- Decision reason: M411 lambda 1e13 combined replay-anchor projection passes exact M267/M264 old-key and M183/M170 first proof gates but is likely retention-heavy because replay trajectory loss is near base and recovery loss is close to M400

## Hypothesis

Combining M409 current-family and M410 old-key replay-failure trajectory anchors will let the recovery-aware exact projection keep exact feasibility while reducing the replay washout observed in M406.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m409_m407_m267_replay_failure_trajectory_anchor/rejected_trajectory_anchor.npz, runs/m410_old_key_replay_failure_trajectory_anchor/old_key_replay_failure_trajectory_anchor.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
- parent_config: experiments/manifests/m409-replay-failure-trajectory-anchor-implementation.json, experiments/manifests/m410-old-key-replay-failure-anchor-implementation.json
- parent_objective: exact lexicographic repair plus replay-failure trajectory-anchor residual
- derived_from: m409-replay-failure-trajectory-anchor-implementation, m410-old-key-replay-failure-anchor-implementation
- blocked_by: m406-recovery-aware-exact-projection-probe, m407-m406-projection-replay-failure-row-audit
- supersedes: None
- invalidates: None

## Success Criteria

- combined anchor contains both M409 and M410 trajectory rows
- projection candidate has exact M297/M270/old-key no-regression versus M400 base
- M267/M264 first replay keeps 17/17 success drops
- old-key compact targeted replay has no accepted regressions
- no PPO is run and no checkpoint is promoted

## Failure Criteria

- combined anchor cannot be loaded by exact_post_ppo_repair
- exact projection has positive exact M297/M270/old-key regression
- M267/M264 wrong-history proof remains washed out
- old-key compact replay remains worse than M400 base
- actor input or output contract changes

## Evidence Gates

- exact M297 no-regression
- exact M270 no-regression
- old-key surrogate no-regression
- M267/M264 first replay
- old-key compact replay targeted gate
- M183/M170 first replay if first gates pass

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m411-combined-replay-aware-projection-probe
- type: gate
- checkpoint: runs/m411_combined_anchor_projection_ltraj1e13_s40_seed10144/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m412_replay_aware_projection_utility_audit
- reason: M411 lambda 1e13 combined replay-anchor projection passes exact M267/M264 old-key and M183/M170 first proof gates but is likely retention-heavy because replay trajectory loss is near base and recovery loss is close to M400

## Next Blocker

m412-replay-aware-projection-utility-audit
