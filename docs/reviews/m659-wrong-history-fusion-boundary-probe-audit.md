# m659-wrong-history-fusion-boundary-probe-audit Research Review

## Summary

- Generated at UTC: 20260524T134801Z
- Type: gate
- Gate tier: proof
- Promotion decision: wrong_history_fusion_boundary_probe_audit_admit_action_divergent_corpus_design
- Decision reason: M659 audits M658 as partial relative signal but absolute wrong-history gap negative and selects action-divergent corpus design

## Hypothesis

M658 shows next_hidden carries more wrong-history signal than fused features, but the current corpus/objective is still too weak to create a strong source-heldout rejected-history branch.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m658_wrong_history_fusion_boundary_probe/summary.json, runs/m658_wrong_history_fusion_boundary_probe/seed_view_summary.csv, docs/m658-wrong-history-fusion-boundary-probe-implementation.md
- parent_config: experiments/manifests/m658-wrong-history-fusion-boundary-probe-implementation.json
- parent_objective: audit negative frozen feature-view comparison probe
- derived_from: m658-wrong-history-fusion-boundary-probe-implementation
- blocked_by: m658-wrong-history-fusion-boundary-probe-implementation
- supersedes: None
- invalidates: None

## Success Criteria

- audit records diagnostic_passed false
- audit records next_hidden relative improvement and absolute threshold failure
- audit selects next branch explicitly
- actor coupling and PPO remain blocked
- research validation passes

## Failure Criteria

- audit treats M658 as promotion evidence
- audit ignores the negative gap_mse results
- audit omits source-heldout source 32 weakness
- audit admits actor coupling or PPO

## Evidence Gates

- classify M658 as negative or partial positive
- separate next_hidden L2 improvement from absolute wrong-history gap failure
- decide whether next branch should mine stronger action-divergent wrong-history corpus or redesign objective
- keep actor coupling and PPO blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not promote checkpoint
- do not claim next_hidden auxiliary-head improvement as closed-loop self-ID proof
- do not tune fused-only contrast coefficients

## Failure Taxonomy

- none

## Scoreboard

- milestone: m659-wrong-history-fusion-boundary-probe-audit
- type: gate
- checkpoint: docs/m659-wrong-history-fusion-boundary-probe-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_fusion_boundary_probe_audit_admit_action_divergent_corpus_design
- reason: M659 audits M658 as partial relative signal but absolute wrong-history gap negative and selects action-divergent corpus design

## Next Blocker

m660-action-divergent-wrong-history-corpus-design
