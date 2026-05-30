# m1720-paper-route-controller-family-off-track-repair-panel-design Research Review

## Summary

- Generated at UTC: 20260530T021535Z
- Type: gate
- Gate tier: process
- Promotion decision: off_track_repair_panel_design_admit_no_rollout_preflight
- Decision reason: M1720 designs 18-base-spec fixed-budget repair panel with baseline conditional-positive controls and wide-relaxed-extended variant

## Hypothesis

A fixed-budget repair panel can be designed from M1718 localized off-track targets while preserving baseline and conditional-positive controls.

## Lineage

- parent_checkpoint: not_applicable_design_only
- parent_dataset: docs/m1719-paper-route-controller-family-off-track-dominance-localization-result-audit.md, runs/m1718_off_track_dominance_localization/repair_target_slices.csv, runs/m1715_controller_family_calibrated_scale_up_execution/episode_rows.csv, runs/m1702_controller_family_task_quality_calibration_preflight/calibration_matrix.csv
- parent_config: experiments/manifests/m1719-paper-route-controller-family-off-track-dominance-localization-result-audit.json
- parent_objective: design fixed-budget off-track repair panel before no-rollout preflight
- derived_from: m1719-paper-route-controller-family-off-track-dominance-localization-result-audit
- blocked_by: need repair panel design before materializing repair subset
- supersedes: direct repair preflight after M1719, direct rollout after M1719
- invalidates: None

## Success Criteria

- docs/m1720-paper-route-controller-family-off-track-repair-panel-design.md exists
- repair panel selected base/source rule is explicit
- repair variant panel is explicit
- baseline and conditional-positive controls are preserved
- wide-relaxed-extended variant availability is addressed
- all twelve controller-family profiles remain controls
- rollout execution training replay PPO promotion private holdout actor-input changes and level3 claims remain blocked

## Failure Criteria

- design omits baseline controls
- design omits conditional-positive controls
- design uses profile ranking to select sources
- design routes directly to rollout
- environment rollout training replay PPO private holdout promotion or actor-input changes occur

## Evidence Gates

- M1720 must design a no-rollout fixed-budget repair panel before materialization
- M1720 must preserve baseline and conditional-positive controls
- M1720 must include the wide-relaxed-extended composite variant only if it exists in the calibration matrix
- M1720 must select repair sources from M1718 target slices without using profile ranking
- M1720 must not run rollout train replay PPO promote use private holdout or change actor inputs
- M1720 must not claim controller-family ranking, paper-level evidence, or level3 self-ID

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment rollout
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1720-paper-route-controller-family-off-track-repair-panel-design
- type: gate
- checkpoint: docs/m1720-paper-route-controller-family-off-track-repair-panel-design.md
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: off_track_repair_panel_design_admit_no_rollout_preflight
- reason: M1720 designs 18-base-spec fixed-budget repair panel with baseline conditional-positive controls and wide-relaxed-extended variant

## Next Blocker

m1721-paper-route-controller-family-off-track-repair-panel-preflight
