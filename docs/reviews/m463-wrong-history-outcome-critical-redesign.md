# m463-wrong-history-outcome-critical-redesign Research Review

## Summary

- Generated at UTC: 20260523T205923Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m464_wrong_history_targeted_pair_triage
- Decision reason: M463 designs separate wrong-history proof from reset/zero diagnostics and sends M464 to targeted pair triage over candidate_pairs.csv

## Hypothesis

M462 shows the current late-reveal selector can find reset/zero-current outcome-critical rows, but wrong-history remains too weak and source-narrow; a redesigned task or selector should target wrong-history continuation failures explicitly.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m462_outcome_critical_selector_fresh_seed10200/compact_corpus.csv, runs/m462_outcome_critical_selector_fresh_seed10200/wrong_history_audit.json
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m462-outcome-critical-selector-repeat-audit.json
- parent_objective: wrong-history outcome-critical task or selector redesign
- derived_from: m462-outcome-critical-selector-repeat-audit
- blocked_by: m462-outcome-critical-selector-repeat-audit
- supersedes: None
- invalidates: None

## Success Criteria

- document root causes for weak wrong-history coverage
- choose one next implementation path with clear evidence discipline
- define source-diverse wrong-history outcome criteria
- define how reset/zero-current evidence remains diagnostic but separate
- no checkpoint is promoted

## Failure Criteria

- design treats M462 wrong-history raw accepted rows as sufficient proof
- design mixes reset/zero-current compact rows into wrong-history pass criteria
- design requires privileged actor inputs
- design skips source-diversity requirements

## Evidence Gates

- analyze why wrong-history rows remain weak after M461 and M462
- design a next task or selector that makes wrong-history intervention outcome-critical
- separate source-diverse wrong-history proof criteria from reset/zero-current diagnostics
- pre-register pass/fail criteria for the next implementation
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not claim wrong-history proof from reset/zero-current rows
- do not accept single-seed or single-label wrong-history margin-only rows as a proof gate

## Failure Taxonomy

- none

## Scoreboard

- milestone: m463-wrong-history-outcome-critical-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m464_wrong_history_targeted_pair_triage
- reason: M463 designs separate wrong-history proof from reset/zero diagnostics and sends M464 to targeted pair triage over candidate_pairs.csv

## Next Blocker

m464-wrong-history-targeted-pair-triage
