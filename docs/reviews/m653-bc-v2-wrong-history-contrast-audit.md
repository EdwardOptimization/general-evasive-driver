# m653-bc-v2-wrong-history-contrast-audit Research Review

## Summary

- Generated at UTC: 20260524T132611Z
- Type: gate
- Gate tier: proof
- Promotion decision: bc_v2_wrong_history_contrast_audit_admit_feature_separability_design
- Decision reason: M653 classifies M652 as normal-retention positive but wrong-history gap negative and selects no-training feature separability audit

## Hypothesis

M652 failed because wrong-history recurrent features remain nearly inseparable under the frozen BC5660 representation, not because normal sequence-delta learning is unavailable.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m652_bc_v2_wrong_history_contrast/summary.json, runs/m652_bc_v2_wrong_history_contrast/seed_summary.csv, runs/m652_bc_v2_wrong_history_contrast/history_variant_summary.csv, docs/m652-bc-v2-wrong-history-contrast-implementation.md
- parent_config: experiments/manifests/m652-bc-v2-wrong-history-contrast-implementation.json
- parent_objective: audit failed frozen-head wrong-history contrast smoke
- derived_from: m652-bc-v2-wrong-history-contrast-implementation
- blocked_by: m652-bc-v2-wrong-history-contrast-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit records 0/3 contrast pass
- audit records normal validation retention
- audit records wrong-history gap failure
- audit chooses feature separability audit or revised objective branch
- research validation passes

## Failure Criteria

- audit ignores wrong-history gap failure
- audit treats normal retention as self-ID proof
- audit admits actor coupling
- audit omits actor checksum and no actor checkpoint checks

## Evidence Gates

- classify the M652 negative result
- separate normal-retention success from wrong-history gap failure
- inspect whether feature separability or objective strength is the likely blocker
- confirm actor checksum remained unchanged
- choose next blocker explicitly

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not increase contrast coefficients before audit
- do not claim self-ID separation from normal target retention

## Failure Taxonomy

- none

## Scoreboard

- milestone: m653-bc-v2-wrong-history-contrast-audit
- type: gate
- checkpoint: docs/m653-bc-v2-wrong-history-contrast-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: bc_v2_wrong_history_contrast_audit_admit_feature_separability_design
- reason: M653 classifies M652 as normal-retention positive but wrong-history gap negative and selects no-training feature separability audit

## Next Blocker

m654-wrong-history-feature-separability-audit-design
