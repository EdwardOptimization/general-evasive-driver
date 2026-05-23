# m390-m267-conflict-residual-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T142318Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m391_full_public_gate_for_m390_a005
- Decision reason: M390 finds step17 endpoint and alpha 0.01 fail M267/M264 but bounded alpha 0.005 passes exact M267/M264 cumulative old-key source-diverse and M183/M170 proof gates

## Hypothesis

The M389 conflict residual can preserve the M267/M264 wrong-history boundary while the M384 old-key recovery residual improves cumulative old-key normal-margin slack, allowing a larger proof-safe no-PPO repair movement than M386's alpha 0.00075 micro step.

## Lineage

- parent_checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: runs/m389_m267_row15_conflict_corpus/current_family_conflict_corpus.npz, runs/m384_old_key_local_recovery_targets/old_key_recovery_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m377_cumulative_gap_tail_v2_old_key_preference_corpus/old_key_preference_corpus.npz
- parent_config: experiments/manifests/m389-m267-row15-conflict-corpus-implementation.json
- parent_objective: test whether old-key recovery plus current-family conflict residual can move beyond the M386 micro base without making M267/M264 row15 safe
- derived_from: m389-m267-row15-conflict-corpus-implementation
- blocked_by: m387-m386-micro-promotion-utility-audit, m388-m267-row15-conflict-residual-design
- supersedes: None
- invalidates: None

## Success Criteria

- produce one or more no-PPO repair/interpolation candidates from the M386 base
- exact M297/M270 and old-key exact surrogate do not regress
- M267/M264 first replay passes 17/17 success drops with row15 still colliding under wrong history
- cumulative old-key replay passes after M267/M264 first replay
- source-diverse protected gate and M183/M170 first replay pass before any full public gate is admitted

## Failure Criteria

- conflict residual is too weak and M267/M264 row15 becomes safe
- conflict residual is too strong and blocks old-key recovery movement
- exact objectives pass but closed-loop replay fails
- actor contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression
- current-family conflict residual finite
- M267/M264 first replay retains 17/17 success drops including row15
- cumulative old-key replay passes
- source-diverse protected gate passes
- M183/M170 first replay passes

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run PPO
- do not promote checkpoint from exact losses alone
- do not lower M267/M264 or old-key thresholds
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m390-m267-conflict-residual-repair-probe
- type: gate
- checkpoint: runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m391_full_public_gate_for_m390_a005
- reason: M390 finds step17 endpoint and alpha 0.01 fail M267/M264 but bounded alpha 0.005 passes exact M267/M264 cumulative old-key source-diverse and M183/M170 proof gates

## Next Blocker

m391-full-public-gate-for-m390-a005
