# M1922 Executable V2 Task-Quality Scenario Redesign Source-Mining Execution Design

- status: completed
- decision: `task_quality_scenario_source_mining_execution_design_admit_execution`
- branch: `paper_route_task_quality_scenario_redesign`
- input template: `configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json`
- execution output dir: `runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution`
- source mining execution in M1922: `false`
- reset/rollout/measured execution in M1922: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

M1923 should run exactly:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_source_mining \
  --candidate-rows configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json \
  --output-dir runs/m1923_executable_v2_task_quality_scenario_redesign_source_mining_execution \
  --support-evidence-artifact configs/executable_v2_task_quality_scenario_redesign_candidates_v0.json \
  --support-evidence-stage task_quality_scenario_redesign_source_mining_v0 \
  --claim-boundary-context project_artifact_execution \
  --next-blocker m1924-executable-v2-task-quality-scenario-redesign-source-mining-result-audit
```

This is grid/source mining only. It must not run environment reset, rollout,
policy action, measured execution, training, replay, PPO, or ranking.

## Target Counts

The input template fixes:

```text
candidate_source_count: 640
candidate_profile_count: 640
role_count: 4
feasibility_tier_count: 5
surface_count: 2
speed_bucket_count: 4
mu_bucket_count: 4
source_split_counts:
  public_debug: 384
  public_gate: 192
  paper_holdout_candidate: 64
```

M1923 execution pass gates:

```text
summary exists
candidate_source_count == 640
candidate_profile_count == 640
role_count == 4
supported_source_count > 0
accepted_cell_count_total > 0
labels_enter_actor_input_count == 0
materialized_row_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
policy_action_executed == false
measured_rollout_started == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

Required artifacts:

```text
summary.json
support_first_source_candidates.csv
support_first_profile_support.csv
support_first_accepted_cells.csv
support_first_blocked_candidates.csv
support_first_role_summary.csv
support_first_materialization_admissibility_input.csv
support_first_claim_boundary.csv
```

## Interpretation Boundary

The existing source-mining helper reports support by source/profile and keeps
the original candidate rows. It does not yet summarize the new
`feasibility_tier_id` and `source_split` fields in `summary.json`.

Therefore:

- M1923 can claim execution completeness and source-mining support counts;
- M1923 cannot claim Tier A/B positive support or Tier C/D near-miss support;
- M1924 must audit the execution by joining output rows back to the M1921
  template metadata before any scenario-quality interpretation.

## Next

Next milestone:

```text
m1923-executable-v2-task-quality-scenario-redesign-source-mining-execution
```

M1923 should run only the command above. If execution passes, M1924 should audit
tier/split/role support before any materialization or ranking.
