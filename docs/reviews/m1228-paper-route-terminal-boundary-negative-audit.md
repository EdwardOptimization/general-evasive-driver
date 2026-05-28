# m1228-paper-route-terminal-boundary-negative-audit Research Review

## Summary

- Generated at UTC: 20260528T080303Z
- Type: gate
- Gate tier: process
- Promotion decision: terminal_boundary_negative_audit_route_to_source_geometry_consistency
- Decision reason: M1228 classifies M1227 as source-geometry replay consistency gap and routes to short-vs-long exact source-geometry audit before any new relocation grid training or proof-criterion weakening

## Hypothesis

M1227 failed because the relocation grid pushed normal-history rollouts past the terminal boundary into collision, so the next step should change the materialization design rather than train or expand the same grid.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1227_terminal_boundary_relocation_smoke/summary.json, runs/m1227_terminal_boundary_relocation_smoke/boundary_relocation_rows.csv, docs/m1227-paper-route-terminal-boundary-relocation-smoke.md
- parent_config: experiments/manifests/m1227-paper-route-terminal-boundary-relocation-smoke.json, configs/paper_route_corrected_profiles/m1207_l3_online_gru.json
- parent_objective: audit why bounded terminal-boundary relocation produced zero accepted wrong-history rows
- derived_from: m1227-paper-route-terminal-boundary-relocation-smoke
- blocked_by: M1227 relocation grid produced all-collision normal and wrong-history rows
- supersedes: immediately expanding relocation replay after zero accepted rows
- invalidates: treating M1227 positive margin gaps from all-collision rows as proof

## Success Criteria

- docs/m1228-paper-route-terminal-boundary-negative-audit.md exists
- M1227 failure mode is classified
- next relocation/source/fallback route is selected
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs

## Failure Criteria

- M1228 trains or tunes profiles
- private holdout is used
- M1227 all-collision rows are claimed as proof
- accepted-row criteria are weakened
- next route is left vague

## Evidence Gates

- M1228 must audit M1227 before another relocation run
- M1228 must preserve actor input contract
- M1228 must not train controllers
- M1228 must not run PPO
- M1228 must not use private holdout
- M1228 must not promote
- M1228 must classify the negative result and select a concrete next route
- M1228 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not weaken accepted-row criteria
- do not treat all-collision margin gaps as proof
- do not expand the grid without diagnosing normal-branch collision

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1228-paper-route-terminal-boundary-negative-audit
- type: gate
- checkpoint: docs/m1228-paper-route-terminal-boundary-negative-audit.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_negative_audit_route_to_source_geometry_consistency
- reason: M1228 classifies M1227 as source-geometry replay consistency gap and routes to short-vs-long exact source-geometry audit before any new relocation grid training or proof-criterion weakening

## Next Blocker

m1229-paper-route-source-geometry-consistency-audit
