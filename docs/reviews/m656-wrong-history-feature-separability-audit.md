# m656-wrong-history-feature-separability-audit Research Review

## Summary

- Generated at UTC: 20260524T133658Z
- Type: gate
- Gate tier: proof
- Promotion decision: wrong_history_feature_separability_audit_admit_fusion_boundary_probe_design
- Decision reason: M656 audits M655 as fusion-boundary blocker and admits frozen fused next-hidden feature-view comparison design

## Hypothesis

M655 shows wrong-history information is present in recurrent hidden state but too compressed at the fused feature and actor-action boundary, so the next branch should address that boundary rather than tuning the frozen head loss.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m655_wrong_history_feature_separability_audit/summary.json, runs/m655_wrong_history_feature_separability_audit/row_feature_separability.csv, docs/m655-wrong-history-feature-separability-audit-implementation.md
- parent_config: experiments/manifests/m655-wrong-history-feature-separability-audit-implementation.json
- parent_objective: audit no-training wrong-history feature separability result
- derived_from: m655-wrong-history-feature-separability-audit-implementation
- blocked_by: m655-wrong-history-feature-separability-audit-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit records M655 classification and key ratios
- audit names the strongest rejected explanations
- audit selects the next branch explicitly
- actor coupling and PPO remain blocked
- research validation passes

## Failure Criteria

- audit ignores the wrong-to-delayed feature and action ratios
- audit admits actor coupling or PPO
- audit treats feature distances as final self-ID proof
- audit omits the source 30 and source 32 split

## Evidence Gates

- classify the M655 fusion-washout result
- separate weak corpus signal from fusion washout and actor-action insensitivity
- decide whether the next branch should target fusion boundary objective corpus refresh or pre-fusion diagnostic
- keep actor coupling and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not tune M652 contrast coefficients from this result alone
- do not claim self-ID proof from feature distance alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m656-wrong-history-feature-separability-audit
- type: gate
- checkpoint: docs/m656-wrong-history-feature-separability-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_feature_separability_audit_admit_fusion_boundary_probe_design
- reason: M656 audits M655 as fusion-boundary blocker and admits frozen fused next-hidden feature-view comparison design

## Next Blocker

m657-wrong-history-fusion-boundary-design
