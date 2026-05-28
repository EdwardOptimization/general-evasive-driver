# m1201-paper-route-profile-separability-audit Research Review

## Summary

- Generated at UTC: 20260528T054650Z
- Type: gate
- Gate tier: process
- Promotion decision: profile_separability_audit_route_to_profile_control_repair_design
- Decision reason: M1201 verifies configs and L2 observation stacks differ but finds L2 current-tiled older-history action sensitivity near zero and M1199 L3_reset_control eval semantics did not enforce every-step reset so diagnostic controls need repair

## Hypothesis

M1199 profile families can be audited for config, observation, and action-level separability before any longer comparison.

## Lineage

- parent_checkpoint: runs/m1199_fair_comparison_pilot/profile_runs
- parent_dataset: runs/m1199_fair_comparison_pilot/profile_seed_rows.csv, runs/m1199_fair_comparison_pilot/eval_rows.csv, runs/m1199_fair_comparison_pilot/profile_aggregate.csv, docs/m1200-paper-route-fair-comparison-pilot-result-audit.md
- parent_config: experiments/manifests/m1200-paper-route-fair-comparison-pilot-result-audit.json
- parent_objective: verify profile separability before longer L0/L1/L2/L3 comparison
- derived_from: m1200-paper-route-fair-comparison-pilot-result-audit
- blocked_by: M1200 classifies L2 window-equivalence as inconclusive but suspicious and L3 reset parity as negative for hidden benefit in M1199
- supersedes: running a longer comparison before checking whether profiles are meaningfully separated
- invalidates: treating M1199 L2 trend as ready for direct scaling without implementation and action-sensitivity audit

## Success Criteria

- docs/m1201-paper-route-profile-separability-audit.md exists
- config differences are summarized
- observation history-stack differences are summarized
- L2 older-history action sensitivity is measured or a tooling blocker is recorded
- L3 reset-hidden action sensitivity is measured or a tooling blocker is recorded
- private holdout remains unused
- no training, PPO, candidate replay, promotion, private holdout, per-profile tuning, or actor-input contract change occurs
- next route is selected

## Failure Criteria

- M1201 trains or tunes profiles
- private holdout is used
- M1201 treats action probes as paper-level evidence
- hidden or oracle actor inputs are introduced
- audit skips L2 or L3 separability

## Evidence Gates

- M1201 may run artifact and checkpoint analysis only
- M1201 must not train controllers
- M1201 must not run PPO
- M1201 must not run candidate replay
- M1201 must not promote
- M1201 must not use private holdout
- M1201 must not tune profiles
- M1201 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not use private holdout
- do not tune profiles
- do not promote
- do not claim profile superiority from action probes
- do not add hidden or oracle actor inputs

## Failure Taxonomy

- metric_artifact

## Scoreboard

- milestone: m1201-paper-route-profile-separability-audit
- type: gate
- checkpoint: runs/m1201_profile_separability_audit/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: profile_separability_audit_route_to_profile_control_repair_design
- reason: M1201 verifies configs and L2 observation stacks differ but finds L2 current-tiled older-history action sensitivity near zero and M1199 L3_reset_control eval semantics did not enforce every-step reset so diagnostic controls need repair

## Next Blocker

m1202-paper-route-profile-control-repair-design
