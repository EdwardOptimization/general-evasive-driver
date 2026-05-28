# m1227-paper-route-terminal-boundary-relocation-smoke Research Review

## Summary

- Generated at UTC: 20260528T075820Z
- Type: gate
- Gate tier: proof
- Promotion decision: terminal_boundary_relocation_smoke_negative_audit_required
- Decision reason: M1227 source and candidate gates passed and relocation replay produced 7200 rows but zero accepted wrong-history rows because all normal and variant rollouts collided so negative audit is required

## Hypothesis

Bounded obstacle/timing relocation can turn M1226 source-diverse action-divergent wrong-history candidates into source-diverse terminal-margin or success-critical rows.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv, runs/m1226_terminal_boundary_candidate_export/summary.json, docs/m1226-paper-route-terminal-boundary-candidate-export.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1226-paper-route-terminal-boundary-candidate-export.json
- parent_objective: bounded terminal-boundary materialization test from M1226 source-diverse action-divergent candidates
- derived_from: m1226-paper-route-terminal-boundary-candidate-export
- blocked_by: M1222 action-divergent rows do not yet show margin-threshold or success-drop degradation under source geometry
- supersedes: directly claiming outcome evidence from M1222 action gaps
- invalidates: assuming action divergence alone is a causal-history proof row

## Success Criteria

- runs/m1227_terminal_boundary_relocation_smoke/summary.json exists
- runs/m1227_terminal_boundary_relocation_smoke/boundary_relocation_rows.csv exists
- source budget and candidate selection pass before replay
- accepted wrong-history rows, if any, are reported with source-diversity accounting
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next audit or fallback route is selected

## Failure Criteria

- M1227 trains or tunes profiles
- private holdout is used
- accepted rows are claimed without source-diversity accounting
- single-source active-set rows are treated as proof
- action divergence is treated as self-identification without outcome degradation
- next route is left vague

## Evidence Gates

- M1227 may run bounded relocation replay only on M1226 exported candidates
- M1227 must preserve actor input contract
- M1227 must not train controllers
- M1227 must not run PPO
- M1227 must not use private holdout
- M1227 must not promote
- M1227 must report source-diverse accepted rows or a clear negative result
- M1227 must not claim self-identification unless outcome degradation is source-diverse and explicitly scoped

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not weaken M1226 candidate thresholds
- do not claim action divergence as outcome evidence
- do not accept a single-source active set as proof

## Failure Taxonomy

- scenario_sampling_failure

## Scoreboard

- milestone: m1227-paper-route-terminal-boundary-relocation-smoke
- type: gate
- checkpoint: runs/m1227_terminal_boundary_relocation_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_relocation_smoke_negative_audit_required
- reason: M1227 source and candidate gates passed and relocation replay produced 7200 rows but zero accepted wrong-history rows because all normal and variant rollouts collided so negative audit is required

## Next Blocker

m1228-paper-route-terminal-boundary-negative-audit
