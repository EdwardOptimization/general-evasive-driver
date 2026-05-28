# m1220-paper-route-current-family-hidden-action-sensitivity-probe Research Review

## Summary

- Generated at UTC: 20260528T071757Z
- Type: gate
- Gate tier: proof
- Promotion decision: hidden_path_exists_but_real_matched_histories_are_action_equivalent
- Decision reason: M1220 finds reset/random/scaled hidden perturbations strongly move action while wrong_matched_history and delayed_history remain below threshold with zero above-threshold rows so outcome rollout is blocked and action-critical source mining is next

## Hypothesis

The current-family actor will show hidden-action sensitivity under reset, shuffled, scaled, or random hidden perturbations even though real wrong/delayed matched histories are action-equivalent.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1217_current_family_matched_current_export/matched_pairs.csv, runs/m1218_current_family_history_action_screen/action_interventions.csv, docs/m1219-paper-route-current-family-action-screen-negative-audit.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1219-paper-route-current-family-action-screen-negative-audit.json
- parent_objective: probe whether the current-family actor reacts to reset shuffled scaled or random hidden perturbations when wrong/delayed histories are action-equivalent
- derived_from: m1219-paper-route-current-family-action-screen-negative-audit
- blocked_by: M1218 shows reset-hidden sensitivity but no real wrong/delayed matched-history action signal
- supersedes: directly changing training objective before hidden-action sensitivity is classified
- invalidates: treating reset-hidden action movement as sufficient self-identification evidence

## Success Criteria

- runs/m1220_current_family_hidden_action_sensitivity_probe/summary.json exists
- runs/m1220_current_family_hidden_action_sensitivity_probe/weight_chunk_summary.csv exists
- runs/m1220_current_family_hidden_action_sensitivity_probe/action_sensitivity_rows.csv exists
- runs/m1220_current_family_hidden_action_sensitivity_probe/variant_summary.csv exists
- runs/m1220_current_family_hidden_action_sensitivity_probe/correlation_summary.csv exists
- reset shuffled scaled random wrong delayed zero-current and zero-action variants are reported
- private holdout remains unused
- no outcome intervention, training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next route milestone is selected

## Failure Criteria

- M1220 trains or tunes profiles
- private holdout is used
- outcome interventions are run
- random/scaled hidden effects are claimed as self-identification
- next route is left vague

## Evidence Gates

- M1220 may run hidden-action sensitivity probe only
- M1220 must include real wrong/delayed history and reset shuffled scaled random hidden variants
- M1220 must include zero-current-response and zero-action-history observation controls
- M1220 must not run outcome interventions
- M1220 must not train controllers
- M1220 must not run PPO
- M1220 must not use private holdout
- M1220 must not promote
- M1220 must not claim self-identification

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run outcome intervention gates
- do not use private holdout
- do not promote
- do not tune profiles
- do not use hidden or oracle actor inputs
- do not claim self-identification from off-manifold hidden perturbations

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1220-paper-route-current-family-hidden-action-sensitivity-probe
- type: gate
- checkpoint: runs/m1220_current_family_hidden_action_sensitivity_probe/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: hidden_path_exists_but_real_matched_histories_are_action_equivalent
- reason: M1220 finds reset/random/scaled hidden perturbations strongly move action while wrong_matched_history and delayed_history remain below threshold with zero above-threshold rows so outcome rollout is blocked and action-critical source mining is next

## Next Blocker

m1221-paper-route-action-critical-hidden-source-design
