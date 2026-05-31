# m1899-executable-v2-support-first-clearance-containment-conflict-localization Research Review

## Summary

- Generated at UTC: 20260531T050930Z
- Type: infrastructure
- Gate tier: infrastructure
- Promotion decision: clearance_containment_conflict_localization_pass_route_to_result_audit
- Decision reason: M1899 classifies 960 M1895 rows with joint 0 clearance-only 784 containment-collision 169 collision-offtrack 7 near-miss rows 429 and keeps ranking blocked

## Hypothesis

A dedicated no-rollout conflict localizer can produce source and slice evidence for the M1895 clearance/containment conflict without ranking controller families.

## Lineage

- parent_checkpoint: not_applicable_clearance_containment_conflict_localization
- parent_dataset: docs/m1898-executable-v2-support-first-clearance-containment-conflict-localization-design.md, runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/episode_rows.csv, runs/m1895_executable_v2_support_first_repaired_bounded_smoke_execution/summary.json
- parent_config: experiments/manifests/m1898-executable-v2-support-first-clearance-containment-conflict-localization-design.json
- parent_objective: implement and run no-rollout localization for clearance-only versus containment-collision conflict
- derived_from: m1898-executable-v2-support-first-clearance-containment-conflict-localization-design
- blocked_by: M1898 requires a dedicated conflict localizer before any ranking or repair execution
- supersedes: manual ad hoc clearance/containment tables
- invalidates: None

## Success Criteria

- src/autodrift/executable_v2_support_first_clearance_containment_conflict_localization.py exists
- tests cover primary conflict class and near-miss aggregation behavior
- runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json exists
- summary reports episode_count 960 and guardrail_violation_count 0
- all rows are assigned exactly one primary conflict class
- required aggregate artifacts are written
- next route is explicit and controller ranking remains blocked

## Failure Criteria

- helper is missing
- focused tests fail
- no-rollout execution drops rows
- classification omits any primary conflict class without explicit zero-count accounting
- helper runs environment reset rollout measured execution training replay PPO or ranking

## Evidence Gates

- M1899 must implement a dedicated no-rollout conflict localizer with focused tests
- M1899 must run the localizer on M1895 episode rows without environment reset or rollout
- M1899 must write summary conflict class near-miss and slice aggregate artifacts
- M1899 must classify the next route without controller ranking
- M1899 must keep training PPO replay private holdout promotion actor-input changes paper claims and level3 self-ID claims blocked

## Holdout Policy

- not_used

## Forbidden Shortcuts

- do not run environment reset
- do not run environment rollout
- do not run measured execution
- do not train
- do not run replay
- do not run PPO
- do not promote a checkpoint
- do not use private holdout
- do not change actor inputs
- do not tune controller profiles
- do not rank controller families
- do not claim paper-level evidence
- do not claim level3 self-identification

## Failure Taxonomy

- none

## Scoreboard

- milestone: m1899-executable-v2-support-first-clearance-containment-conflict-localization
- type: infrastructure
- checkpoint: runs/m1899_executable_v2_support_first_clearance_containment_conflict_localization/summary.json
- success_rate: None
- termination_rate: None
- clearance_margin_mean: None
- reset_success: None
- zero_wheel_success: None
- zero_all_success: None
- wheel_gain_mu: None
- decision: clearance_containment_conflict_localization_pass_route_to_result_audit
- reason: M1899 classifies 960 M1895 rows with joint 0 clearance-only 784 containment-collision 169 collision-offtrack 7 near-miss rows 429 and keeps ranking blocked

## Next Blocker

m1900-executable-v2-support-first-clearance-containment-conflict-localization-result-audit
