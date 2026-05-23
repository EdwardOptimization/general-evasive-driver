# m466-near-boundary-wrong-history-redesign Research Review

## Summary

- Generated at UTC: 20260523T211239Z
- Type: infrastructure
- Gate tier: generalization
- Promotion decision: admit_m467_near_boundary_wrong_history_selector
- Decision reason: M466 shows M465 has near-boundary wrong-history rows but zero accepted low-margin degradation so proof needs normal-margin-aware selection

## Hypothesis

Wrong-history proof remains weak because current pair selection does not condition on near-boundary normal-history outcomes; a normal-margin-aware redesign is needed before another outcome probe.

## Lineage

- parent_checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- parent_dataset: runs/m465_targeted_wrong_history_selector/wrong_history_evidence_audit.json, runs/m465_targeted_wrong_history_selector/wrong_history_compact.csv
- parent_config: configs/m457_history_necessity_late_reveal_zero_relvel.json, experiments/manifests/m465-targeted-wrong-history-outcome-probe.json
- parent_objective: near-boundary wrong-history proof redesign
- derived_from: m465-targeted-wrong-history-outcome-probe
- blocked_by: m465-targeted-wrong-history-outcome-probe
- supersedes: None
- invalidates: None

## Success Criteria

- document the high-slack failure mode from M465
- define a near-boundary normal-history margin ceiling
- define source-diverse wrong-history outcome pass criteria
- choose the next implementation path
- no checkpoint is promoted

## Failure Criteria

- design treats M465 margin-only rows as sufficient proof
- design hides wrong-history failure behind reset/zero-current aggregates
- design requires privileged actor inputs
- design skips source diversity

## Evidence Gates

- analyze why M465 wrong-history rows remain high-slack margin-only
- design a near-boundary wrong-history mining or selector path
- define normal-margin ceiling and source-diverse outcome criteria
- separate high-margin diagnostics from proof rows
- no checkpoint promotion

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not promote checkpoint
- do not change actor input/output contract
- do not add hidden or oracle actor inputs
- do not accept high-margin-only wrong-history rows as proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m466-near-boundary-wrong-history-redesign
- type: infrastructure
- checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: admit_m467_near_boundary_wrong_history_selector
- reason: M466 shows M465 has near-boundary wrong-history rows but zero accepted low-margin degradation so proof needs normal-margin-aware selection

## Next Blocker

m467-near-boundary-wrong-history-selector
