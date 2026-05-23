# m407-m406-projection-replay-failure-row-audit Research Review

## Summary

- Generated at UTC: 20260523T155649Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m408_replay_aware_projection_residual_design
- Decision reason: M407 classifies M406 failure as broad wrong-history washout: 16/17 M267/M264 rows become safe and old-key has 6 wrong-history-safe regressions plus one normal failure

## Hypothesis

M406 failed because exact one-step/corpus objectives do not represent the closed-loop replay rows that protect wrong-history collision-side behavior and old-key normal-branch margins.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt, runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
- parent_dataset: runs/m406_a01proj_m267_m264_first_replay/boundary_replay_rows.csv, runs/m406_a01proj_old_key_replay_gate/old_key_replay_comparison_rows.csv, runs/m406_repair_from_alpha01_s40_seed10137/action_alignment.csv
- parent_config: experiments/manifests/m406-recovery-aware-exact-projection-probe.json
- parent_objective: audit which closed-loop replay rows fail despite exact M297/M270/old-key feasibility
- derived_from: m406-recovery-aware-exact-projection-probe
- blocked_by: m406-recovery-aware-exact-projection-probe
- supersedes: None
- invalidates: None

## Success Criteria

- identify the M267/M264 rows whose wrong-history branch became successful
- identify the old-key rows causing accepted regressions and lower-tail gap failure
- separate normal-branch margin failures from wrong-history sensitivity loss
- pre-register the next repair design or corpus refresh based on row-level evidence

## Failure Criteria

- audit cannot locate replay rows
- audit relies on private holdout
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- no checkpoint promotion
- classify M267/M264 wrong-history replay failures
- classify old-key accepted regressions
- decide whether next residual should be trajectory/replay-aware rather than exact-corpus scalar

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint
- do not lower exact or replay thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- proof_washout
- objective_overfit
- protected_key_window_failure

## Scoreboard

- milestone: m407-m406-projection-replay-failure-row-audit
- type: gate
- checkpoint: runs/m406_repair_from_alpha01_s40_seed10137/candidate_checkpoint.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m408_replay_aware_projection_residual_design
- reason: M407 classifies M406 failure as broad wrong-history washout: 16/17 M267/M264 rows become safe and old-key has 6 wrong-history-safe regressions plus one normal failure

## Next Blocker

m408-replay-aware-projection-residual-design
