# m388-m267-row15-conflict-residual-design Research Review

## Summary

- Generated at UTC: 20260523T140000Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: admit_m389_m267_row15_conflict_corpus_implementation
- Decision reason: M388 designs current-family conflict corpus and residual for M267/M264 row15 and row6 so old-key recovery cannot make wrong-history rows safe

## Hypothesis

A conflict-aware repair design can expose M267/M264 row15 as a first-class active constraint, preventing old-key recovery updates from making current-family wrong-history rollouts safe.

## Lineage

- parent_checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- parent_dataset: runs/m387_m386_micro_promotion_utility_audit/summary.json, runs/m387_m386_micro_promotion_utility_audit/m267_row15_alpha_trace.csv
- parent_config: experiments/manifests/m387-m386-micro-promotion-utility-audit.json
- parent_objective: design a repair objective that treats M267/M264 row15 as an active wrong-history boundary while preserving old-key recovery
- derived_from: m387-m386-micro-promotion-utility-audit
- blocked_by: m387-m386-micro-promotion-utility-audit
- supersedes: None
- invalidates: None

## Success Criteria

- define the residual or corpus needed for M267/M264 row15 and related rows
- state how it composes with old-key recovery without changing actor inputs
- pre-register acceptance gates before implementation
- research validation passes

## Failure Criteria

- design relies on threshold relaxation
- design relies on hidden actor inputs
- design ignores cumulative old-key recovery
- research validation fails

## Evidence Gates

- no PPO run
- preserve actor contract
- design must keep M267/M264 success-drop retention authoritative
- design must keep cumulative old-key replay authoritative

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not lower M267/M264 thresholds
- do not make wrong-history rows safe
- do not add hidden or oracle actor inputs
- do not run PPO in the design milestone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m388-m267-row15-conflict-residual-design
- type: infrastructure
- checkpoint: runs/m385_recovery_repair_micro_interpolation/checkpoints/alpha_0_00075.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m389_m267_row15_conflict_corpus_implementation
- reason: M388 designs current-family conflict corpus and residual for M267/M264 row15 and row6 so old-key recovery cannot make wrong-history rows safe

## Next Blocker

m389-m267-row15-conflict-corpus-implementation
