# m369-hard-row-weighted-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T120839Z
- Type: gate
- Gate tier: proof
- Promotion decision: admit_m370_full_public_gate_for_m369_a400
- Decision reason: M369 hard-row weighted repair direct endpoint fails old-key replay but bounded alpha 0.4 passes old-key source-diverse and first replay proof gates; alpha 0.6 first tested old-key gap-p10 failure

## Hypothesis

Hard-row weighted old-key repair can recover or enlarge the alpha 0.2 direction by increasing wrong-history pressure on the M366 sign-crossing row while preserving exact M297/M270 and old-key surrogate gates.

## Lineage

- parent_checkpoint: runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_1.pt, runs/m364_old_key_aware_repair_interpolation/checkpoints/alpha_0_2.pt
- parent_dataset: runs/m368_old_key_preference_corpus_hard_row/old_key_preference_corpus.npz, runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz, runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz, runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv
- parent_config: experiments/manifests/m368-old-key-hard-row-feedback-implementation.json
- parent_objective: probe whether hard-row branch weights can repair the M366 alpha 0.2 wrong-history sign crossing without PPO
- derived_from: m368-old-key-hard-row-feedback-implementation
- blocked_by: m368-old-key-hard-row-feedback-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- hard-row weighted repair candidate passes exact M297/M270 and weighted old-key surrogate gates
- closed-loop old-key replay has zero accepted regressions at an alpha greater than 0.1 or exposes a stronger repair candidate
- source-diverse and first replay gates are run if old-key replay passes
- failure is classified if the weighted surrogate remains insensitive to the terminal sign crossing
- research validation passes

## Failure Criteria

- hard-row weighted repair cannot move beyond alpha 0.1 without old-key replay failure
- exact objectives regress
- weighted old-key surrogate is insensitive to the M366 hard row
- actor input contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression
- weighted old-key surrogate no-regression
- old-key neighborhood targeted replay and replay-gate adapter
- source-diverse protected gates if old-key replay passes
- M183/M170 and M267/M264 first replay gates if proof gates pass
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote directly
- do not run PPO
- do not lower old-key replay thresholds
- do not skip closed-loop old-key replay
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m369-hard-row-weighted-repair-probe
- type: gate
- checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m370_full_public_gate_for_m369_a400
- reason: M369 hard-row weighted repair direct endpoint fails old-key replay but bounded alpha 0.4 passes old-key source-diverse and first replay proof gates; alpha 0.6 first tested old-key gap-p10 failure

## Next Blocker

m370-full-public-gate-for-m369-a400
