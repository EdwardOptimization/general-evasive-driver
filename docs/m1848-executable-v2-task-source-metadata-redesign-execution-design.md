# M1848 Executable V2 Task-Source Metadata Redesign Execution Design

- status: completed
- decision: `task_source_metadata_redesign_execution_design_admit_run`
- branch: `paper_route_executable_v2_task_source_metadata_redesign`
- project artifact execution run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1847 implemented the support-first metadata helper. M1848 pre-registers the
exact command to run it over M1843 support evidence. This milestone does not run
the command.

## Input Artifacts

```text
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_profile_summary.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_label_counts.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_reject_reason_counts.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json
```

No explicit source-rows file is supplied. The helper will derive source rows
from the profile summary with:

```text
default_source_role: stable_aes_only
```

This is intentional: M1849 should test whether the current M1843 evidence blocks
the same stable AES-only sources before any future materialization.

## Output Directory

```text
runs/m1849_executable_v2_task_source_metadata_redesign
```

## Exact M1849 Command

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

## Expected Counts

M1849 should pass as execution if:

| field | expected |
| --- | ---: |
| `input_source_count` | 2 |
| `input_profile_count` | 24 |
| `supported_source_count` | 0 |
| `unsupported_source_count` | 2 |
| `materialization_admissible_source_count` | 0 |
| `materialization_blocked_source_count` | 2 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |
| `environment_reset_started` | false |
| `policy_action_executed` | false |

Expected claim-boundary context:

```text
project_artifact_execution
```

## Expected Output Artifacts

```text
summary.json
task_source_support_contract.csv
task_source_role_contract.csv
task_source_materialization_admissibility.csv
task_source_blocked_sources.csv
task_source_claim_boundary.csv
```

## Follow-Up

If M1849 runs, route to:

```text
m1850-executable-v2-task-source-metadata-redesign-result-audit
```

M1850 should audit whether the helper correctly blocks the two unsupported
stable AES-only sources and whether a new support-mining/materialization branch
is admissible.

## Guardrails

- project artifact execution: `false`
- source repair payload generated: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- exact support-first metadata redesign execution command;
- M1849 project-artifact metadata execution is admitted.

Unsupported:

- execution result;
- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
