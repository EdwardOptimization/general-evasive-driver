# m442-active-boundary-v2-projection-probe Research Review

## Summary

- Generated at UTC: 20260523T191244Z
- Type: gate
- Gate tier: proof
- Promotion decision: reject_m442_v2_tail_candidate_stop_active_boundary_branch
- Decision reason: M442 exact projection passes M267 and M183 but old-key compact is 39 of 40 and recovery retained 0.111895 is below M438 r0015 0.120957 so v2 branch is rejected

## Hypothesis

The v2 active-boundary residual can make a looser profile proof-safe while retaining more M406 recovery utility than M438 r0015.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt
- parent_dataset: runs/m441_active_boundary_v2_residual/active_boundary_v2_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
- parent_config: experiments/manifests/m441-active-boundary-v2-residual-implementation.json
- parent_objective: active-boundary v2 no-PPO projection
- derived_from: m441-active-boundary-v2-residual-implementation
- blocked_by: m441-active-boundary-v2-residual-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- candidate exact M297/M270/old-key no-regression passes
- M267/M264 first replay remains 17 of 17
- old-key compact replay remains 40 of 40
- M183/M170 first replay remains 17 of 17
- minimum useful if recovery retained vs M406 exceeds 0.120957
- strong evidence if recovery retained vs M406 reaches at least 0.174354
- primary pass if recovery retained vs M406 reaches at least 0.20

## Failure Criteria

- exact objectives regress before replay
- active-boundary v2 exact loss improves while old-key normal success drops
- M267/M264 wrong-history rows become safe
- old-key compact exposes 10004 10023 or 9998 boundary failures
- recovery retained remains at or below M438 r0015

## Evidence Gates

- exact M297/M270/old-key no-regression
- active-boundary v2 residual tracked
- M267/M264 first replay 17 of 17
- old-key compact replay 40 of 40
- old-key replay gate pass
- M183/M170 first replay 17 of 17
- recovery retained vs M406 compared with M438 r0015

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs
- do not make replay labels actor inputs

## Failure Taxonomy

- protected_key_window_failure
- objective_overfit

## Scoreboard

- milestone: m442-active-boundary-v2-projection-probe
- type: gate
- checkpoint: runs/m442_tail_r0010_active_boundary_v2_l1e12_s40_seed10162/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: reject_m442_v2_tail_candidate_stop_active_boundary_branch
- reason: M442 exact projection passes M267 and M183 but old-key compact is 39 of 40 and recovery retained 0.111895 is below M438 r0015 0.120957 so v2 branch is rejected

## Next Blocker

m443-active-boundary-v2-stop-audit
