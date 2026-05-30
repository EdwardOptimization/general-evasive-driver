# M1843 Executable V2 Reset-Time AES Feasibility Scan Execution

- status: completed
- decision: `reset_time_aes_feasibility_scan_no_support_route_to_result_audit`
- branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- artifact: `runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_reset_time_aes_feasibility_scan \
  --repaired-specs runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json \
  --reset-rows runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1843_executable_v2_reset_time_aes_feasibility_scan \
  --distance-min 1.0 \
  --distance-max 60.0 \
  --distance-count 120 \
  --half-width-min 0.2 \
  --half-width-max 1.4 \
  --half-width-count 61 \
  --max-boundary-examples-per-profile 8 \
  --expected-target-source-count 2 \
  --expected-target-profile-count-total 24 \
  --next-blocker m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit
```

## Summary

```text
result_class: reset_time_aes_feasibility_scan_no_support
target_source_count: 2
target_profile_count_total: 24
feasible_profile_count_total: 0
feasible_source_count: 0
grid_cell_count_total: 175680
accepted_cell_count_total: 0
guardrail_violation_count: 0
```

Expected counts matched:

```text
expected_source_match: true
expected_profile_match: true
```

## Label And Reject Counts

Across all scanned cells:

| label | count |
| --- | ---: |
| `aeb_feasible` | 159820 |
| `drift_required` | 284 |
| `unavoidable` | 15576 |

Reject reasons:

| reject reason | count |
| --- | ---: |
| `aeb_feasible_rejected` | 159820 |
| `label_not_allowed` | 15860 |

There were no accepted `aes_feasible` cells. The grid did find non-AEB regions,
but they were classified as `drift_required` or `unavoidable`, not stable AES.

## Source Summary

Both target sources have zero feasible profiles:

| source | profiles | feasible profiles | accepted cells |
| --- | ---: | ---: | ---: |
| `m1771-bp1-00` | 12 | 0 | 0 |
| `m1771-bp1-02` | 12 | 0 | 0 |

## Artifacts

```text
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_profile_summary.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_source_summary.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_accepted_cells.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_label_counts.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_reject_reason_counts.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_boundary_examples.csv
runs/m1843_executable_v2_reset_time_aes_feasibility_scan/reset_time_aes_feasibility_claim_boundary.csv
```

## Claim Boundary

Supported:

```text
M1843 ran the pre-registered no-reset feasibility scan and found no AES-only
support in the specified conditional grid.
```

Unsupported:

```text
source repair success
repaired reset feasibility
measured execution
controller-family ranking
paper-level result
level3 self-identification evidence
```

## Follow-Up

Route to:

```text
m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit
```

M1844 should decide whether this is enough to close the current source-repair
route and pivot to task/source metadata redesign or branch synthesis.
