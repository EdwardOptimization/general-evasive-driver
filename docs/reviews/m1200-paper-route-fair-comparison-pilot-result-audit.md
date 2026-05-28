# m1200-paper-route-fair-comparison-pilot-result-audit Research Review

## Summary

- Generated at UTC: 20260528T054154Z
- Type: gate
- Gate tier: process
- Promotion decision: fair_comparison_pilot_audit_route_to_profile_separability_audit
- Decision reason: M1200 audits M1199 as a valid public pilot trend but blocks direct scaling because L2 window-equivalence is inconclusive but suspicious and L3 reset parity is negative for recurrent-hidden benefit in this pilot

## Hypothesis

The M1199 public pilot can be audited into a safe next-route decision without expanding its claim scope.

## Lineage

- parent_checkpoint: runs/m1199_fair_comparison_pilot/profile_runs
- parent_dataset: runs/m1199_fair_comparison_pilot/summary.json, runs/m1199_fair_comparison_pilot/profile_seed_rows.csv, runs/m1199_fair_comparison_pilot/eval_rows.csv, runs/m1199_fair_comparison_pilot/profile_aggregate.csv
- parent_config: experiments/manifests/m1199-paper-route-fair-comparison-pilot-run.json, docs/m1199-paper-route-fair-comparison-pilot-run.md
- parent_objective: audit the first fair public profile-comparison pilot before increasing budget or making stronger claims
- derived_from: m1199-paper-route-fair-comparison-pilot-run
- blocked_by: M1199 produced public pilot trends but also L2 window-equivalence and L3 reset-parity patterns that need audit
- supersedes: directly scaling the strongest M1199 public pilot profile without checking profile separation
- invalidates: claiming recurrent-hidden benefit or paper-level profile ranking directly from M1199

## Success Criteria

- docs/m1200-paper-route-fair-comparison-pilot-result-audit.md exists
- M1199 aggregate and seed-level trends are summarized
- L2 window-equivalence and L3 reset-control parity are explicitly audited
- private holdout remains unused
- no controller training, candidate replay, PPO, promotion, private holdout, per-profile tuning, or actor-input contract change occurs
- next route is selected

## Failure Criteria

- M1200 trains or tunes profiles
- private holdout is used
- M1199 is framed as paper-level evidence
- hidden or oracle actor inputs are introduced
- audit skips the L2 window-equivalence or L3 reset-parity issues

## Evidence Gates

- M1200 may audit M1199 artifacts only
- M1200 must not train controllers
- M1200 must not run PPO
- M1200 must not run candidate replay
- M1200 must not promote
- M1200 must not use private holdout
- M1200 must not tune profiles based on M1199 results
- M1200 must not claim paper-level evidence or self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not scale L2 before auditing window-equivalence
- do not discard L3 before auditing reset-control parity
- do not use private holdout
- do not tune one profile and compare against frozen profiles
- do not promote any M1199 checkpoint
- do not claim recurrent-belief advantage or self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1200-paper-route-fair-comparison-pilot-result-audit
- type: gate
- checkpoint: docs/m1200-paper-route-fair-comparison-pilot-result-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: fair_comparison_pilot_audit_route_to_profile_separability_audit
- reason: M1200 audits M1199 as a valid public pilot trend but blocks direct scaling because L2 window-equivalence is inconclusive but suspicious and L3 reset parity is negative for recurrent-hidden benefit in this pilot

## Next Blocker

m1201-paper-route-profile-separability-audit
