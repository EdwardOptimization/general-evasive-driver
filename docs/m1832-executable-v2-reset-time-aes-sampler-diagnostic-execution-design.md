# M1832 Executable V2 Reset-Time AES Sampler Diagnostic Execution Design

- status: completed
- decision: `reset_time_aes_sampler_diagnostic_execution_design_admit_run`
- branch: `paper_route_executable_v2_reset_time_aes_sampler_diagnostic`
- project artifact diagnostic run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1831 implemented and tested the reset-time AES sampler diagnostic helper.
M1832 pre-registers the exact command to run that helper over the M1825 repaired
payload and M1828 reset rows. This milestone does not run the diagnostic.

## Input Artifacts

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

## Output Directory

```text
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic
```

## Exact M1833 Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_time_aes_sampler_diagnostic \
  --repaired-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic \
  --max-example-rows-per-spec 8 \
  --next-blocker m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit
```

This diagnostic command replays sampler candidate attempts from reset RNG state.
It must not call `AutoDriftEnv.reset`, step the environment, or execute a policy
action.

## Expected Counts

M1833 should pass only if:

| field | expected |
| --- | ---: |
| `target_failed_aes_row_count` | 24 |
| `diagnostic_target_row_count` | 24 |
| `source_count` | 2 |
| `guardrail_violation_count` | 0 |
| `environment_reset_started` | false |
| `policy_action_executed` | false |

Expected output artifacts:

```text
summary.json
aes_source_diagnostic_targets.csv
offline_density_rows.csv
reset_time_attempt_summary.csv
reset_time_reject_reason_counts.csv
reset_time_label_counts.csv
reset_time_candidate_examples.csv
claim_boundary.csv
```

## Follow-Up

If M1833 runs, route to:

```text
m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit
```

M1834 should decide whether the evidence supports source repair v2, adapter
instrumentation repair, or another diagnostic pass. It should not run reset.

## Guardrails

- project artifact diagnostic execution: `false`
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

- exact reset-time AES sampler diagnostic command and expected counts;
- M1833 diagnostic execution is admitted.

Unsupported:

- diagnostic result;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
