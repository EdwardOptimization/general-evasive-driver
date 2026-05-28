# m1226-paper-route-terminal-boundary-candidate-export Research Review

## Summary

- Generated at UTC: 20260528T074853Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: terminal_boundary_candidate_export_passed
- Decision reason: M1226 exported 274 relocation-compatible terminal-boundary candidates across 110 physical pairs with source-diversity gate passed and no relocation replay training PPO promotion private holdout or actor-input changes

## Hypothesis

A thin adapter can export M1222 action-divergent rows into relocation-compatible candidate artifacts with sufficient source diversity for a later bounded materialization run.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv, docs/m1225-paper-route-terminal-boundary-materialization-design.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1225-paper-route-terminal-boundary-materialization-design.json
- parent_objective: implement/export M1222 action-divergent candidates into relocation-compatible terminal-boundary candidate CSV
- derived_from: m1225-paper-route-terminal-boundary-materialization-design
- blocked_by: M1222 candidate_scores.csv is not directly compatible with source_balanced_boundary_relocation_surface
- supersedes: feeding M1222 candidate_scores.csv directly into relocation tooling
- invalidates: assuming field-name compatibility between normal_success_boundary_source_miner and source_balanced_boundary_relocation_surface

## Success Criteria

- runs/m1226_terminal_boundary_candidate_export/summary.json exists
- runs/m1226_terminal_boundary_candidate_export/candidate_outcomes.csv exists
- source-diversity pass/fail is reported
- focused tests for the adapter pass
- private holdout remains unused
- no relocation replay, source mining, outcome intervention, training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next route milestone is selected

## Failure Criteria

- M1226 runs relocation replay
- M1226 trains or tunes profiles
- private holdout is used
- candidate export omits source-diversity accounting
- exported candidates are claimed as proof rows
- next route is left vague

## Evidence Gates

- M1226 may implement/export adapter artifacts only
- M1226 must not run relocation replay
- M1226 must preserve actor input contract
- M1226 must include source-diversity accounting
- M1226 must not train controllers
- M1226 must not run PPO
- M1226 must not use private holdout
- M1226 must not promote
- M1226 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run relocation replay
- do not use private holdout
- do not promote
- do not add hidden or oracle actor inputs
- do not weaken M1222 action thresholds
- do not treat exported candidates as proof rows

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1226-paper-route-terminal-boundary-candidate-export
- type: infrastructure
- checkpoint: runs/m1226_terminal_boundary_candidate_export/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: terminal_boundary_candidate_export_passed
- reason: M1226 exported 274 relocation-compatible terminal-boundary candidates across 110 physical pairs with source-diversity gate passed and no relocation replay training PPO promotion private holdout or actor-input changes

## Next Blocker

m1227-paper-route-terminal-boundary-relocation-smoke
