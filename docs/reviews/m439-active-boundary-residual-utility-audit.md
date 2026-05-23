# m439-active-boundary-residual-utility-audit Research Review

## Summary

- Generated at UTC: 20260523T185336Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m440_active_boundary_v2_residual_design
- Decision reason: M439 finds active-boundary v1 repairs r0015 but not tail_r0010 and high scalar weight creates normal-branch collisions so v2 needs row-specific design

## Hypothesis

M438's active-boundary residual is useful but under-specified: it can repair r0015, but tail_r0010 still fails because the residual does not directly encode enough closed-loop margin slack for 10004 and 10023.

## Lineage

- parent_checkpoint: runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt, runs/m438_tail_r0010_active_boundary_lactive1e12_s40_seed10159/candidate_checkpoint.pt, runs/m438_tail_r0010_active_boundary_lactive1e14_s40_seed10160/candidate_checkpoint.pt
- parent_dataset: runs/m437_active_boundary_residual/active_boundary_corpus.npz, runs/m438_r0015_lactive1e12_old_key_targeted_replay/guard_results.csv, runs/m438_tail_lactive1e12_old_key_targeted_replay/guard_results.csv, runs/m438_tail_lactive1e14_old_key_targeted_replay/guard_results.csv
- parent_config: experiments/manifests/m438-active-boundary-projection-probe.json
- parent_objective: active-boundary residual utility and proof alignment audit
- derived_from: m438-active-boundary-projection-probe
- blocked_by: m438-active-boundary-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- explain why r0015 passes while tail_r0010 fails
- measure whether active-boundary exact loss tracks closed-loop old-key failures
- classify high active-boundary weight normal-branch collisions
- recommend a concrete next residual or reject further active-boundary tuning

## Failure Criteria

- audit cannot distinguish objective underweighting from objective misspecification
- audit recommends another scalar sweep without row-level evidence
- audit recommends PPO before proof residual design
- actor input or output contract changes

## Evidence Gates

- row-level comparison of r0015 pass and tail_r0010 failure
- active-boundary loss and margin alignment audit
- classification of whether next residual should use row-specific weights or margin terms
- no PPO and no promotion

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

- milestone: m439-active-boundary-residual-utility-audit
- type: gate
- checkpoint: runs/m438_r0015_active_boundary_lactive1e12_s40_seed10161/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m440_active_boundary_v2_residual_design
- reason: M439 finds active-boundary v1 repairs r0015 but not tail_r0010 and high scalar weight creates normal-branch collisions so v2 needs row-specific design

## Next Blocker

m440-active-boundary-v2-residual-design
