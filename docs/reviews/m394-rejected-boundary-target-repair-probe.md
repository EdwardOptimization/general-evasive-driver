# m394-rejected-boundary-target-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T145518Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m395_full_public_gate_for_m394_s02a010
- Decision reason: M394 bounds the rejected-boundary repair to s02 alpha 0.1 after exact M267/M264 old-key source-diverse and M183/M170 proof gates pass; full public gate required before promotion

## Hypothesis

The M393 collision-side rejected-history targets give the current-family conflict residual a useful signal to create row15/row6 wrong-history collision slack while preserving exact M297/M270 and old-key proof.

## Lineage

- parent_checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- parent_dataset: runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz, runs/m393_current_family_rejected_boundary_targets/current_family_conflict_rows.csv, runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
- parent_config: experiments/manifests/m393-current-family-rejected-boundary-target-export.json
- parent_objective: no-PPO exact repair/interpolation using replay-selected current-family rejected-boundary targets
- derived_from: m393-current-family-rejected-boundary-target-export
- blocked_by: m393-current-family-rejected-boundary-target-export
- supersedes: None
- invalidates: None

## Success Criteria

- run exact repair from the current public base with M393 conflict corpus and M384 old-key recovery corpus
- select a bounded candidate or interpolation alpha that passes exact M297/M270 no-regression
- retain M267/M264 first replay 17/17
- retain cumulative old-key, source-diverse protected, and M183/M170 proof gates
- record the first failing alpha or boundary if no promotable proof candidate is found

## Failure Criteria

- all nonzero repair or interpolation candidates fail exact M297/M270
- M267/M264 row15 or row6 wrong-history rollout becomes successful
- old-key proof regresses
- candidate movement is indistinguishable from a no-op and requires another audit
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression versus current base
- M267/M264 first replay retains 17/17 wrong-history success drops
- cumulative old-key replay retains zero accepted regressions and gap floor
- source-diverse protected gate retains 5/5
- M183/M170 first replay retains 17/17

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote a checkpoint without a later full public gate
- do not lower M267/M264 or old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m394-rejected-boundary-target-repair-probe
- type: gate
- checkpoint: runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m395_full_public_gate_for_m394_s02a010
- reason: M394 bounds the rejected-boundary repair to s02 alpha 0.1 after exact M267/M264 old-key source-diverse and M183/M170 proof gates pass; full public gate required before promotion

## Next Blocker

m395-full-public-gate-for-m394-s02a010
