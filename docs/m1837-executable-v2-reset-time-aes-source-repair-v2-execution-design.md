# M1837 Executable V2 Reset-Time AES Source Repair V2 Execution Design

- status: completed
- decision: `reset_time_aes_source_repair_v2_execution_design_admit_run`
- branch: `paper_route_executable_v2_reset_time_aes_source_repair_v2`
- project artifact execution: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1836 implemented and tested the reset-time AES source repair v2 helper. M1837
pre-registers the exact command to run that helper on the M1825 repaired payload
and M1828 reset rows. This milestone does not run the helper.

## Input Artifacts

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

## Output Directory

```text
runs/m1838_executable_v2_reset_time_aes_source_repair_v2
```

## Exact M1838 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_time_aes_source_repair_v2 \
  --repaired-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1838_executable_v2_reset_time_aes_source_repair_v2 \
  --target-source-count 2 \
  --target-profile-count 12 \
  --target-repaired-spec-count 36 \
  --main-attempt-budget 10000 \
  --next-blocker m1839-executable-v2-reset-time-aes-source-repair-v2-result-audit
```

This command must run no environment reset, no rollout, no policy action, no
training, no replay, no PPO, and no ranking. It only replays reset-time obstacle
sampler attempts from reset RNG state.

## Expected Counts

M1838 should evaluate:

| field | expected |
| --- | ---: |
| target source count | 2 |
| target profile count per source | 12 |
| total target profiles | 24 |
| repaired executable spec count | 36 |
| main attempt budget | 10000 |
| guardrail violation count | 0 |

`result_class` may be either:

```text
reset_time_aes_source_repair_v2_pass
reset_time_aes_source_repair_v2_fail
```

A fail result is still useful if all artifacts and guardrails are clean. M1839
must audit the result before any reset rerun.

## Expected Output Artifacts

```text
summary.json
reset_time_aes_source_repair_targets.csv
reset_time_aes_source_repair_candidate_scores.csv
reset_time_aes_source_repair_specs.json
reset_time_aes_source_repair_specs.csv
repaired_targeted_reset_executable_v2_panel_specs.json
reset_time_aes_source_repair_claim_boundary.csv
```

The summary must include:

```text
attempt_count_by_label
attempt_count_by_reject_reason
row_count_by_label
row_count_by_reject_reason
summary_aggregation_version = row_and_attempt_counts_v1
```

## Follow-Up

If M1838 runs, route to:

```text
m1839-executable-v2-reset-time-aes-source-repair-v2-result-audit
```

M1839 should decide whether the repaired payload is admitted to a reset-only
preflight, whether the source repair needs another implementation pass, or
whether the branch should synthesize and pivot.

## Guardrails

- project artifact repair execution: `false`
- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- exact source repair v2 command and expected counts;
- M1838 project artifact execution is admitted.

Unsupported:

- source repair result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
