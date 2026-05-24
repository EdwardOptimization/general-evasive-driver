# m657-wrong-history-fusion-boundary-probe-design Research Review

## Summary

- Generated at UTC: 20260524T133940Z
- Type: infrastructure
- Gate tier: proof
- Promotion decision: wrong_history_fusion_boundary_probe_design_admit_m658
- Decision reason: M657 designs frozen fused next-hidden and fused-plus-hidden diagnostic head comparison before any actor coupling

## Hypothesis

If M655 is a fusion-boundary blocker, a diagnostic head trained on next_hidden or fused_plus_next_hidden should create stronger wrong-history separation than a head trained on fused actor features alone.

## Lineage

- parent_checkpoint: runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
- parent_dataset: runs/m655_wrong_history_feature_separability_audit/summary.json, docs/m656-wrong-history-feature-separability-audit.md
- parent_config: experiments/manifests/m656-wrong-history-feature-separability-audit.json
- parent_objective: design frozen feature-view comparison probe after M655 fusion washout
- derived_from: m656-wrong-history-feature-separability-audit
- blocked_by: m656-wrong-history-feature-separability-audit
- supersedes: None
- invalidates: None

## Success Criteria

- design defines fused next_hidden and concat feature views
- design defines normal target and wrong-history contrast metrics for each view
- design defines source-heldout comparison against M652 fused-feature baseline
- design keeps actor coupling and PPO blocked
- research validation passes

## Failure Criteria

- design admits actor updates
- design omits the fused-feature baseline
- design omits source 30 versus source 32 reporting
- design claims promotion from auxiliary probe results

## Evidence Gates

- design frozen auxiliary probe comparing fused feature next-hidden and concat views
- keep BC5660 actor frozen
- reuse M641 source-balanced sequence corpus
- report normal retention and wrong-history gaps by view source and split
- keep actor coupling PPO and promotion blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not update actor parameters
- do not run PPO
- do not promote checkpoint
- do not use metadata as actor input
- do not treat auxiliary head success as closed-loop self-ID proof

## Failure Taxonomy

- none

## Scoreboard

- milestone: m657-wrong-history-fusion-boundary-probe-design
- type: infrastructure
- checkpoint: docs/m657-wrong-history-fusion-boundary-probe-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: wrong_history_fusion_boundary_probe_design_admit_m658
- reason: M657 designs frozen fused next-hidden and fused-plus-hidden diagnostic head comparison before any actor coupling

## Next Blocker

m658-wrong-history-fusion-boundary-probe-implementation
