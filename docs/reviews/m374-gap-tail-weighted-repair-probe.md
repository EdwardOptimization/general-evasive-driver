# m374-gap-tail-weighted-repair-probe Research Review

## Summary

- Generated at UTC: 20260523T122736Z
- Type: gate
- Gate tier: proof
- Promotion decision: not_applicable
- Decision reason: M374 can admit a full proof or public gate only if the gap-tail weighted candidate passes closed-loop old-key replay, then source-diverse and first replay gates; it cannot promote directly.

## Hypothesis

Gap-tail weighted old-key repair can produce a candidate beyond the M370 alpha 0.4 base while retaining the old-key compact gap lower-tail distribution that rejected alpha 0.6.

## Lineage

- parent_checkpoint: runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_4.pt, runs/m369_hard_row_repair_interpolation/checkpoints/alpha_0_6.pt
- parent_dataset: runs/m373_old_key_preference_corpus_gap_tail/old_key_preference_corpus.npz, runs/m373_gap_tail_overlay/old_key_feedback_overlay.csv, runs/m371_alpha06_gap_audit/alpha04_alpha06_gap_audit_rows.csv
- parent_config: experiments/manifests/m373-old-key-gap-tail-feedback-implementation.json
- parent_objective: probe whether gap-tail branch weights can repair old-key compact lower-tail erosion without PPO
- derived_from: m373-old-key-gap-tail-feedback-implementation
- blocked_by: m373-old-key-gap-tail-feedback-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- gap-tail weighted repair candidate passes exact M297/M270 and weighted old-key surrogate gates
- closed-loop old-key replay has zero accepted regressions and compact gap p10 above the registered threshold at an alpha greater than 0.4 or exposes a bounded candidate
- source-diverse and first replay gates are run if old-key replay passes
- failure is classified if weighted exact metrics improve but closed-loop old-key gap tail still erodes
- research validation passes

## Failure Criteria

- gap-tail weighted repair cannot move beyond alpha 0.4 without old-key compact gap-p10 failure
- exact objectives regress
- weighted old-key surrogate is insensitive to M371 gap-tail rows
- actor input contract changes
- research validation fails

## Evidence Gates

- no PPO run
- exact M297/M270 no-regression
- weighted old-key surrogate no-regression
- closed-loop old-key compact replay and replay-gate adapter
- source-diverse protected gates if old-key replay passes
- M183/M170 and M267/M264 first replay gates if proof gates pass
- preserve actor input contract

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not promote directly
- do not run PPO
- do not lower old-key gap-p10 threshold
- do not skip closed-loop old-key replay
- do not change actor inputs

## Failure Taxonomy

- none

## Scoreboard

- No scoreboard row recorded.

## Next Blocker

pending M374 gap-tail weighted repair probe
