# m651-bc-v2-wrong-history-contrast-design Research Review

## Summary

- Generated at UTC: 20260524T131341Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: bc_v2_wrong_history_contrast_design_admit_m652
- Decision reason: M651 designs a frozen-head contrast objective with normal target retention and wrong-history rejection while keeping actor coupling blocked

## Hypothesis

A head-only contrast objective can preserve normal sequence-delta learnability while forcing wrong-history features not to predict the same corrective sequence.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m649_bc_v2_head_only_repeat/summary.json, runs/m649_bc_v2_head_only_repeat/wrong_history_source_summary.csv, docs/m650-bc-v2-head-only-repeat-audit.md
- parent_config: experiments/manifests/m650-bc-v2-head-only-repeat-audit.json
- parent_objective: design wrong-history contrast objective before any actor coupling
- derived_from: m650-bc-v2-head-only-repeat-audit
- blocked_by: m650-bc-v2-head-only-repeat-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies contrast loss for wrong_matched_history rows
- design specifies normal target retention thresholds
- design specifies wrong-history gap thresholds
- design preserves frozen actor checksum gate
- research validation passes

## Failure Criteria

- design admits actor coupling
- design ignores wrong-history rows
- design collapses delayed and wrong variants without justification
- design omits source-balanced weighting
- design changes actor inputs

## Evidence Gates

- design normal-target and wrong-history rejection losses
- separate wrong_matched_history rows from delayed_history rows
- preserve frozen-actor head-only scope
- pre-register normal-target retention and wrong-history gap thresholds
- keep actor coupling and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train in design milestone
- do not update actor parameters in later head-only contrast smoke
- do not force delayed-history rows to behave like wrong-history rows without audit
- do not promote checkpoint
- do not use source ids target labels or split labels as actor inputs

## Failure Taxonomy

- none

## Scoreboard

- milestone: m651-bc-v2-wrong-history-contrast-design
- type: infrastructure
- checkpoint: docs/m651-bc-v2-wrong-history-contrast-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_wrong_history_contrast_design_admit_m652
- reason: M651 designs a frozen-head contrast objective with normal target retention and wrong-history rejection while keeping actor coupling blocked

## Next Blocker

m652-bc-v2-wrong-history-contrast-implementation
