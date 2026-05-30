# M1833 Executable V2 Reset-Time AES Sampler Diagnostic Execution

- status: completed
- decision: `reset_time_aes_sampler_diagnostic_pass_route_to_result_audit`
- branch: `paper_route_executable_v2_reset_time_aes_sampler_diagnostic`
- artifact: `runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/summary.json`
- result class: `reset_time_aes_sampler_diagnostic_pass`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1833 ran the exact reset-time AES sampler diagnostic command registered in
M1832 over the M1825 repaired targeted reset payload and M1828 failed reset
rows. The run diagnoses why the repaired AES rows still fail the reset-time
sampler. It does not call `AutoDriftEnv.reset`, step an environment, execute a
policy action, or train anything.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_time_aes_sampler_diagnostic \
  --repaired-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic \
  --max-example-rows-per-spec 8 \
  --next-blocker m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit
```

## Output Artifacts

```text
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/summary.json
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/aes_source_diagnostic_targets.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/offline_density_rows.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_attempt_summary.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_reject_reason_counts.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_label_counts.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_candidate_examples.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/claim_boundary.csv
```

## Summary

| field | value |
| --- | ---: |
| `target_failed_aes_row_count` | 24 |
| `diagnostic_target_row_count` | 24 |
| `source_count` | 2 |
| `attempt_count_per_row` | 10000 |
| `total_attempt_count` | 240000 |
| `accepted_count` | 0 |
| `guardrail_violation_count` | 0 |

Both AES failure sources were diagnosed:

```text
m1771-bp1-00
m1771-bp1-02
```

For every one of the 24 failed AES profile rows, the replayed reset-time sampler
attempts produced:

```text
label: aeb_feasible
reject_reason: aeb_feasible_rejected
accepted_count: 0
```

The detailed CSVs therefore support a stronger statement than the top-level
row-count summary: across 240000 replayed candidates, every sampled candidate
was in the AEB-feasible region and was rejected by `require_aeb_infeasible`.
No reset-time `aes_feasible` candidate was observed for either failed AES source.

## Interpretation

M1825's offline density proxy was not sufficient for reset-time AES support.
The repaired AES ranges have nonzero offline density, but under the reset-time
speed and friction draws used by M1828/M1833 they land in the AEB-feasible band,
not the AES-only band required by the executable reset task.

This points away from more attempt budget or blind range widening. The next
audit should decide whether source repair v2 must search directly against
reset-time sampler acceptance and the `require_aeb_infeasible` gate.

## Guardrails

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

- M1833 diagnostic execution completed;
- the diagnostic covered all 24 failed AES rows from M1828;
- both persistent AES sources were diagnosed;
- reset-time rejection is dominated by `aeb_feasible_rejected`;
- detailed attempt tables show 240000 rejected AEB-feasible candidates and zero
  accepted candidates.

Unsupported:

- repaired reset feasibility;
- source repair success;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Follow-Up

Route to:

```text
m1834-executable-v2-reset-time-aes-sampler-diagnostic-result-audit
```

M1834 should audit the detailed CSVs, classify the summary row-count aggregation
weakness, and decide the next repair route without running reset, rollout,
training, replay, PPO, ranking, or paper-level claims.
