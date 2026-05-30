# M1849 Executable V2 Task-Source Metadata Redesign Execution

- status: completed
- decision: `task_source_metadata_redesign_blocks_unsupported_sources_route_to_audit`
- branch: `paper_route_executable_v2_task_source_metadata_redesign`
- artifact: `runs/m1849_executable_v2_task_source_metadata_redesign/summary.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_task_source_metadata_redesign \
  --profile-summary runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_profile_summary.csv \
  --label-counts runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_label_counts.csv \
  --reject-reason-counts runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_reject_reason_counts.csv \
  --output-dir runs/m1849_executable_v2_task_source_metadata_redesign \
  --support-evidence-artifact runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json \
  --support-evidence-stage pre_materialization_scan \
  --claim-boundary-context project_artifact_execution \
  --default-source-role stable_aes_only \
  --next-blocker m1850-executable-v2-task-source-metadata-redesign-result-audit
```

## Summary

```text
contract_id: executable_v2_support_first_task_source_v1
input_source_count: 2
input_profile_count: 24
supported_source_count: 0
unsupported_source_count: 2
unknown_source_count: 0
materialization_admissible_source_count: 0
materialization_blocked_source_count: 2
labels_enter_actor_input_count: 0
ranking_admissible_by_default_count: 0
claim_boundary_context: project_artifact_execution
guardrail_violation_count: 0
```

Both sources were blocked:

| source | role | status | admissible | failure |
| --- | --- | --- | --- | --- |
| `m1771-bp1-00` | `stable_aes_only` | `unsupported` | false | `label_role_mismatch` |
| `m1771-bp1-02` | `stable_aes_only` | `unsupported` | false | `label_role_mismatch` |

## Claim Boundary

The helper emitted context-aware claim boundary rows:

```text
project_artifact_execution / project_artifact_execution / true
project_artifact_execution / source_repair_payload_generated / false
project_artifact_execution / controller_family_ranking / false
```

This fixes the M1843 context-wording issue for the metadata helper path.

## Artifacts

```text
runs/m1849_executable_v2_task_source_metadata_redesign/summary.json
runs/m1849_executable_v2_task_source_metadata_redesign/task_source_support_contract.csv
runs/m1849_executable_v2_task_source_metadata_redesign/task_source_role_contract.csv
runs/m1849_executable_v2_task_source_metadata_redesign/task_source_materialization_admissibility.csv
runs/m1849_executable_v2_task_source_metadata_redesign/task_source_blocked_sources.csv
runs/m1849_executable_v2_task_source_metadata_redesign/task_source_claim_boundary.csv
```

## Follow-Up

Route to:

```text
m1850-executable-v2-task-source-metadata-redesign-result-audit
```

M1850 should decide whether this support-first metadata gate is sufficient to
start a new support-mining/materialization branch.
