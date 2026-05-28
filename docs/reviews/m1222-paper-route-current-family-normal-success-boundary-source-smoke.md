# m1222-paper-route-current-family-normal-success-boundary-source-smoke Research Review

## Summary

- Generated at UTC: 20260528T072715Z
- Type: gate
- Gate tier: proof
- Promotion decision: normal_success_boundary_source_negative_admit_audit
- Decision reason: M1222 finds 45 near-boundary preferred windows and 274 all-action-threshold rows but zero margin-threshold or success-drop rows so accepted_rows is zero and the result is action-gap-positive outcome-gap-negative

## Hypothesis

A broader current-family normal-success boundary source miner can find real wrong-history action/outcome-critical rows that M1217 matched-current pairs missed.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1220_current_family_hidden_action_sensitivity_probe/variant_summary.csv, docs/m1221-paper-route-action-critical-hidden-source-design.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1221-paper-route-action-critical-hidden-source-design.json
- parent_objective: run current-family normal-success boundary source mining after M1221 selects this route
- derived_from: m1221-paper-route-action-critical-hidden-source-design, m667-normal-success-boundary-source-miner-implementation
- blocked_by: M1220 shows M1217 real matched histories are action-equivalent, M1221 selects broader current-family normal-success boundary source mining before outcome gates
- supersedes: directly running persistent outcome intervention from M1217 rows, directly using reset/random hidden perturbations as training or self-ID evidence
- invalidates: assuming the M1217 matched-current source is sufficient for causal-history outcome testing

## Success Criteria

- runs/m1222_current_family_normal_success_boundary_source_smoke/summary.json exists
- runs/m1222_current_family_normal_success_boundary_source_smoke/normal_window_summary.csv exists
- runs/m1222_current_family_normal_success_boundary_source_smoke/candidate_scores.csv exists
- runs/m1222_current_family_normal_success_boundary_source_smoke/normal_success_boundary_rows.csv exists
- normal-success window coverage is reported
- accepted row count and diversity are reported
- actor checksum is unchanged
- private holdout remains unused
- no training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next route milestone is selected

## Failure Criteria

- M1222 trains or tunes profiles
- private holdout is used
- PPO is run
- actor checksum changes
- hidden/oracle fields enter actor input
- action/margin thresholds are weakened after seeing the result
- source mining alone is claimed as self-identification
- next route is left vague

## Evidence Gates

- M1222 may run normal_success_boundary_source_miner only
- M1222 must use P0 human-view no-wheel actor inputs unchanged
- M1222 must keep hidden labels and scenario metadata outside actor observation
- M1222 must not train controllers
- M1222 must not run PPO
- M1222 must not promote
- M1222 must not use private holdout
- M1222 must not claim self-identification
- M1222 must classify a negative result before any next training or outcome step

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run PPO
- do not run persistent outcome gates from M1217 rows
- do not use private holdout
- do not promote
- do not tune actor inputs
- do not add hidden or oracle actor inputs
- do not weaken action or margin thresholds after seeing the result
- do not claim self-identification from source mining alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1222-paper-route-current-family-normal-success-boundary-source-smoke
- type: gate
- checkpoint: runs/m1222_current_family_normal_success_boundary_source_smoke/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: normal_success_boundary_source_negative_admit_audit
- reason: M1222 finds 45 near-boundary preferred windows and 274 all-action-threshold rows but zero margin-threshold or success-drop rows so accepted_rows is zero and the result is action-gap-positive outcome-gap-negative

## Next Blocker

m1223-paper-route-current-family-boundary-source-negative-audit
