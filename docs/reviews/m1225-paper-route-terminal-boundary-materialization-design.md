# m1225-paper-route-terminal-boundary-materialization-design Research Review

## Summary

- Generated at UTC: 20260528T073716Z
- Type: gate
- Gate tier: process
- Promotion decision: terminal_boundary_materialization_design_admit_adapter_export
- Decision reason: M1225 audits M1222 candidate compatibility and selects a thin adapter/export route to relocation-compatible terminal-boundary candidates with source-diversity and active-set-collapse guards before any relocation replay

## Hypothesis

M1222 action-divergent rows can be turned into a bounded terminal-boundary materialization test with explicit source-diversity and active-set-collapse guards.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: docs/m1224-paper-route-causal-history-evidence-synthesis.md, runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv, runs/m1222_current_family_normal_success_boundary_source_smoke/normal_window_rows.csv
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1224-paper-route-causal-history-evidence-synthesis.json
- parent_objective: design the terminal-boundary materialization branch selected by M1224
- derived_from: m1224-paper-route-causal-history-evidence-synthesis
- blocked_by: M1222 has action-divergent rows but no outcome degradation, M1224 selects terminal-boundary materialization as the next branch
- supersedes: continuing the closed paper_route_causal_history_evidence branch, training from M1222 action-only rows
- invalidates: claiming M1222 action divergence is enough for causal-history proof

## Success Criteria

- docs/m1225-paper-route-terminal-boundary-materialization-design.md exists
- M1222 candidate compatibility is audited
- existing-tool versus adapter route is selected
- source-diversity and active-set-collapse gates are specified
- private holdout remains unused
- no source mining, relocation replay, outcome intervention, training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next route milestone is selected

## Failure Criteria

- M1225 trains or tunes profiles
- private holdout is used
- relocation replay is run
- self-identification is claimed
- M1177 active-set-collapse lesson is omitted
- next route is left vague

## Evidence Gates

- M1225 may design terminal-boundary materialization only
- M1225 must preserve the P0 human-view no-wheel actor contract
- M1225 must decide whether existing relocation tooling can consume M1222 rows or an adapter is required
- M1225 must include source-diversity and active-set-collapse guards
- M1225 must not run source mining or relocation replay
- M1225 must not train controllers
- M1225 must not run PPO
- M1225 must not use private holdout
- M1225 must not promote
- M1225 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run relocation replay
- do not use private holdout
- do not promote
- do not tune actor inputs
- do not add hidden or oracle actor inputs
- do not use action-only rows as proof
- do not ignore M1177 active-set collapse risk

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1225-paper-route-terminal-boundary-materialization-design
- type: gate
- checkpoint: docs/m1225-paper-route-terminal-boundary-materialization-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_materialization_design_admit_adapter_export
- reason: M1225 audits M1222 candidate compatibility and selects a thin adapter/export route to relocation-compatible terminal-boundary candidates with source-diversity and active-set-collapse guards before any relocation replay

## Next Blocker

m1226-paper-route-terminal-boundary-candidate-export
