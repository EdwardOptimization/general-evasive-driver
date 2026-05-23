# m403-old-key-normal-recovery-weight-sweep Research Review

## Summary

- Generated at UTC: 20260523T153841Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m404_recovery_exact_conflict_row_audit
- Decision reason: M403 finds no proof-safe recovery-weight candidate: low weights move opposite target while high weights improve old-key but violate exact M297/M270 and later M267/M264

## Hypothesis

Increasing old-key recovery residual pressure can correct the underweighted M398 target direction without washing out current-family wrong-history proof or old-key compact replay.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_targets.csv, runs/m402_old_key_recovery_alignment_audit/alignment_rows.csv, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
- parent_config: experiments/manifests/m402-old-key-normal-recovery-alignment-audit.json
- parent_objective: test whether stronger old-key recovery residual pressure can move policy actions toward M398 targets while preserving proof gates
- derived_from: m402-old-key-normal-recovery-alignment-audit
- blocked_by: m402-old-key-normal-recovery-alignment-audit
- supersedes: None
- invalidates: None

## Success Criteria

- run no-PPO exact repair variants with stronger old-key recovery pressure
- identify whether any bounded candidate moves the 9958 preferred action toward the M398 recovery target
- retain exact M297/M270/old-key no-regression
- retain cumulative old-key compact and M267/M264 first replay proof gates
- record first failing alpha or conflict if no proof-safe candidate exists

## Failure Criteria

- all recovery-weight variants either remain opposite to the target or fail exact/proof gates
- current-family wrong-history rows become safe
- old-key compact accepted regressions appear before useful action movement
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270/old-key no-regression versus M400 base
- policy action on case 9958 moves toward M398 recovery target
- cumulative old-key replay retains zero accepted regressions
- M267/M264 first replay retains 17/17 wrong-history success drops

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint without a later full public gate
- do not lower thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- objective_overfit
- proof_washout

## Scoreboard

- milestone: m403-old-key-normal-recovery-weight-sweep
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m404_recovery_exact_conflict_row_audit
- reason: M403 finds no proof-safe recovery-weight candidate: low weights move opposite target while high weights improve old-key but violate exact M297/M270 and later M267/M264

## Next Blocker

m404-recovery-exact-conflict-row-audit
