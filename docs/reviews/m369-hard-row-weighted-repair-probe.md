# m369-hard-row-weighted-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T120147Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M369 completes by running a no-PPO hard-row weighted repair probe, checking closed-loop old-key replay for feasible candidates, classifying the result, and registering the next blocker.

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

- No scoreboard row recorded.

## Next Blocker

pending M369 hard-row weighted repair probe
