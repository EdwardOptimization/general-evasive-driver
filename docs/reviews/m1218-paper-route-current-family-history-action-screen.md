# m1218-paper-route-current-family-history-action-screen Research Review

## Summary

- Generated at UTC: 20260528T070805Z
- Type: gate
- Gate tier: proof
- Promotion decision: current_family_history_action_screen_negative_route_to_audit
- Decision reason: M1218 finds wrong_matched_history mean action distance 0.001075 and delayed_history 0.000154 with zero above-threshold rows while reset_hidden is strong at 0.041795 mean and 629 above-threshold rows so outcome rollout is blocked

## Hypothesis

On the M1217 current-family matched-current surface, wrong or delayed recurrent history will produce measurable action changes beyond zero-current-response and zero-action controls.

## Lineage

- parent_checkpoint: runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111600/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111601/checkpoint.pt, runs/m1212_corrected_profile_repeat/profile_runs/L3_online_gru/seed_111602/checkpoint.pt
- parent_dataset: runs/m1217_current_family_matched_current_export/matched_pairs.csv, docs/m1217-paper-route-current-family-matched-current-export.md
- parent_config: configs/paper_route_corrected_profiles/m1207_l3_online_gru.json, experiments/manifests/m1217-paper-route-current-family-matched-current-export.json
- parent_objective: screen whether reset delayed wrong-history zero-response and zero-action interventions change current-family L3 actions on matched-current pairs
- derived_from: m1217-paper-route-current-family-matched-current-export
- blocked_by: M1217 pair mining passes and admits action-level history-intervention screening
- supersedes: running persistent outcome intervention before action-screen admission
- invalidates: claiming history causality from pair mining alone

## Success Criteria

- runs/m1218_current_family_history_action_screen/summary.json exists
- runs/m1218_current_family_history_action_screen/action_interventions.csv exists
- runs/m1218_current_family_history_action_screen/variant_summary.csv exists
- wrong_matched_history or delayed_history action_distance_mean >= 0.01 on at least one checkpoint-target group
- wrong_matched_history or delayed_history above_threshold_count >= 16 on at least one checkpoint-target group with threshold 0.02
- zero_current_response and zero_action_history positive controls are reported
- private holdout remains unused
- no outcome intervention, training, PPO, promotion, private holdout, profile tuning, or actor-input contract expansion occurs
- next outcome-gate or negative-audit milestone is selected

## Failure Criteria

- M1218 trains or tunes profiles
- private holdout is used
- outcome interventions are run
- only zero-current-response is action-sensitive and wrong/delayed history is not
- self-identification is claimed from action distance

## Evidence Gates

- M1218 may run action-level history interventions only
- M1218 must use M1217 matched-current pairs
- M1218 must include reset_hidden wrong_matched_history delayed_history zero_current_response and zero_action_history variants
- M1218 must not run outcome interventions
- M1218 must not train controllers
- M1218 must not run PPO
- M1218 must not use private holdout
- M1218 must not promote
- M1218 must not claim self-identification from action distance alone

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not train
- do not run outcome intervention gates
- do not use private holdout
- do not promote
- do not tune profiles
- do not use hidden or oracle actor inputs
- do not claim self-identification from action screen alone

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1218-paper-route-current-family-history-action-screen
- type: gate
- checkpoint: runs/m1218_current_family_history_action_screen/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: current_family_history_action_screen_negative_route_to_audit
- reason: M1218 finds wrong_matched_history mean action distance 0.001075 and delayed_history 0.000154 with zero above-threshold rows while reset_hidden is strong at 0.041795 mean and 629 above-threshold rows so outcome rollout is blocked

## Next Blocker

m1219-paper-route-current-family-action-screen-negative-audit
