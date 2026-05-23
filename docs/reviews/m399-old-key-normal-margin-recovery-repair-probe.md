# m399-old-key-normal-margin-recovery-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T152125Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m400_full_public_gate_for_m399_s02a050
- Decision reason: M399 selects bounded alpha 0.05 after exact old-key M267/M264 M183/M170 and source-diverse proof gates pass; alpha 0.1 first fails old-key case 9958

## Hypothesis

The M398 normal-margin recovery corpus gives exact repair a useful signal to create old-key normal-branch slack beyond the M395 alpha 0.1 base while the M393 current-family conflict residual preserves wrong-history collision-side behavior.

## Lineage

- parent_checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- parent_dataset: runs/m398_old_key_normal_margin_recovery_targets/old_key_recovery_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
- parent_config: experiments/manifests/m398-old-key-normal-margin-recovery-target-export.json
- parent_objective: probe no-PPO exact repair with refreshed old-key normal-margin recovery targets
- derived_from: m398-old-key-normal-margin-recovery-target-export
- blocked_by: m398-old-key-normal-margin-recovery-target-export
- supersedes: None
- invalidates: None

## Success Criteria

- run exact repair from the current public base with M398 recovery and M393 conflict corpora
- select a bounded candidate or interpolation alpha that passes exact M297/M270/old-key no-regression
- retain M267/M264 first replay 17/17
- retain cumulative old-key, source-diverse protected, and M183/M170 proof gates
- record the first failing alpha or boundary if no proof-safe candidate is found

## Failure Criteria

- all nonzero repair candidates fail exact M297/M270/old-key no-regression
- old-key normal-branch cliff rows still fail before useful movement
- M267/M264 row15 or row6 wrong-history rollout becomes successful
- candidate movement is indistinguishable from a no-op
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression versus current base
- old-key surrogate no-regression versus current base
- M267/M264 first replay retains 17/17 wrong-history success drops
- cumulative old-key replay retains zero accepted regressions and gap floor
- source-diverse protected gate retains 5/5
- M183/M170 first replay retains 17/17

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint without a later full public gate
- do not lower replay or old-key thresholds
- do not add hidden or oracle actor inputs
- do not replace direct steer/throttle/brake output

## Failure Taxonomy

- none

## Scoreboard

- milestone: m399-old-key-normal-margin-recovery-repair-probe
- type: gate
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m400_full_public_gate_for_m399_s02a050
- reason: M399 selects bounded alpha 0.05 after exact old-key M267/M264 M183/M170 and source-diverse proof gates pass; alpha 0.1 first fails old-key case 9958

## Next Blocker

m400-full-public-gate-for-m399-s02a050
