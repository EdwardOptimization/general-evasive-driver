# M2011 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Measured Outcome Localization V2 Design

- status: completed
- decision: `task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2_command_design_admit_no_rerun_execution`
- branch: `paper_route_task_quality_calibrated_repaired_outcome_support_v2_localization`
- source measured run: `runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat`
- output directory: `runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2`
- measured execution in M2011: `false`
- environment rollout in M2011: `false`
- policy action execution in M2011: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design

M2011 freezes a no-rerun localization command over the completed M2009
measured-execution artifacts. The command reuses the existing calibrated
repaired measured-outcome localizer and must only read `summary.json` and
`episode_rows.csv`; it must not reset the environment, run rollout, execute
policy actions, train, replay, or promote a checkpoint.

## Frozen Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_repaired_measured_outcome_localization \
  --summary runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/summary.json \
  --episode-rows runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/episode_rows.csv \
  --output-dir runs/m2012_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_outcome_localization_v2 \
  --target-episode-count 960 \
  --target-profile-count 12 \
  --target-source-kind-count 4 \
  --target-role-count 4 \
  --target-normalized-surface-count 3 \
  --target-sampled-label-count 4 \
  --next-blocker m2013-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-outcome-localization-v2-result-audit
```

## Pass Gates

M2012 should pass only if the no-rerun localizer reports:

```text
result_class: task_quality_calibrated_repaired_measured_outcome_localization_pass
episode_count: 960
profile_count: 12
source_kind_count: 4
role_count: 4
normalized_surface_count: 3
sampled_label_count: 4
outcome_counts_match_source_summary: true
all_selected_metrics_finite: true
required_aggregate_files_written: true
guardrail_violation_count: 0
```

The expected guardrail booleans remain:

```text
environment_reset_started: false
environment_rollout_started: false
policy_action_executed: false
measured_rollout_started: false
training_started: false
replay_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
profile_specific_tuning: false
controller_family_ranking_claim_made: false
paper_level_claim_made: false
level3_self_id_claim_made: false
```

## Interpretation Boundary

M2012 can identify comparison-ready or repair-support slices. It cannot by
itself rank controller families, make paper-level benchmark claims, establish
finite-window vs GRU conclusions, or support level3 self-identification.

Any localization result must be audited in M2013 before choosing a repair,
comparison, or redesign route.

## Next

Next milestone:

```text
m2012-executable-v2-task-quality-calibrated-repaired-outcome-support-measured-outcome-localization-v2
```
