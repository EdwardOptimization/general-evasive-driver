# m654-wrong-history-feature-separability-audit-design Research Review

## Summary

- Generated at UTC: 20260524T132938Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: wrong_history_feature_separability_audit_design_admit_m655
- Decision reason: M654 designs raw-hidden next-hidden fused-feature and actor-action distance audit to localize where wrong-history signal collapses before actor coupling

## Hypothesis

The M652 wrong-history contrast failure is caused by weak normal-vs-wrong separability in frozen BC5660 recurrent features.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m652_bc_v2_wrong_history_contrast/summary.json, runs/m652_bc_v2_wrong_history_contrast/history_variant_summary.csv, docs/m653-bc-v2-wrong-history-contrast-audit.md
- parent_config: experiments/manifests/m653-bc-v2-wrong-history-contrast-audit.json
- parent_objective: design wrong-history frozen-feature separability audit before changing contrast objective
- derived_from: m653-bc-v2-wrong-history-contrast-audit
- blocked_by: m653-bc-v2-wrong-history-contrast-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design specifies feature and hidden distance metrics
- design specifies source split and variant breakdowns
- design specifies comparison to delayed-history rows
- design keeps actor coupling blocked
- research validation passes

## Failure Criteria

- design admits training
- design omits wrong-history feature metrics
- design omits delayed-history comparison
- design weakens actor input contract

## Evidence Gates

- design no-training frozen-feature separability audit
- measure normal-vs-wrong feature and hidden distances
- report by source split and variant
- compare wrong-history rows to delayed-history rows
- keep actor coupling and contrast coefficient changes blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not update actor parameters
- do not change contrast coefficients before separability audit
- do not promote checkpoint

## Failure Taxonomy

- none

## Scoreboard

- milestone: m654-wrong-history-feature-separability-audit-design
- type: infrastructure
- checkpoint: docs/m654-wrong-history-feature-separability-audit-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_feature_separability_audit_design_admit_m655
- reason: M654 designs raw-hidden next-hidden fused-feature and actor-action distance audit to localize where wrong-history signal collapses before actor coupling

## Next Blocker

m655-wrong-history-feature-separability-audit-implementation
