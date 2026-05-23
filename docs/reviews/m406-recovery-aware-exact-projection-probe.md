# m406-recovery-aware-exact-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T155332Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_m406_projection_candidate_admit_replay_failure_row_audit
- Decision reason: M406 exact-feasible projection moves toward M398 recovery targets but fails closed-loop proof: M267/M264 drops to 1/17 and old-key compact has 7 accepted regressions

## Hypothesis

A recovery-heavy raw proposal may be projected back to exact M297/M270 feasibility while retaining some movement toward the M398 recovery target.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt, runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_6.pt, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m405-recovery-aware-exact-projection-design.json
- parent_objective: probe recovery-aware exact projection from recovery-heavy raw candidates
- derived_from: m405-recovery-aware-exact-projection-design
- blocked_by: m405-recovery-aware-exact-projection-design
- supersedes: None
- invalidates: None

## Success Criteria

- run no-PPO repair_from_raw projection from at least the alpha 0.1 recovery-heavy raw candidate
- select a candidate only if exact M297/M270/old-key no-regression passes
- verify movement toward the M398 recovery target on 9958
- retain cumulative old-key compact replay and M267/M264 first replay
- record collapse-to-base or replay failure if projection cannot produce a useful candidate

## Failure Criteria

- projection collapses to the M400 base with no recovery movement
- projection keeps recovery movement but exact remains violated
- projection is exact-feasible but fails old-key or M267/M264 replay
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270/old-key no-regression
- distance to M398 recovery action on 9958 decreases versus M400 base
- cumulative old-key compact replay passes
- M267/M264 first replay retains 17/17

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint without a later full public gate
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- objective_overfit
- proof_washout
- protected_key_window_failure

## Scoreboard

- milestone: m406-recovery-aware-exact-projection-probe
- type: gate
- checkpoint: runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m406_projection_candidate_admit_replay_failure_row_audit
- reason: M406 exact-feasible projection moves toward M398 recovery targets but fails closed-loop proof: M267/M264 drops to 1/17 and old-key compact has 7 accepted regressions

## Next Blocker

m407-m406-projection-replay-failure-row-audit
