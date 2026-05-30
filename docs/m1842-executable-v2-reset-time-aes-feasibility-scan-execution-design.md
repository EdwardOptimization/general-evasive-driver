# M1842 Executable V2 Reset-Time AES Feasibility Scan Execution Design

- status: completed
- decision: `reset_time_aes_feasibility_scan_execution_design_admit_run`
- branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- project artifact scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1841 implemented the no-reset reset-time AES feasibility scan helper. M1842
pre-registers the exact command to run that helper over the M1825 repaired
payload and M1828 reset-stress rows. This milestone does not run the scan.

## Input Artifacts

```text
runs/m1825_executable_v2_stable_source_targeted_reset_sampler_repair/repaired_targeted_reset_executable_v2_panel_specs.json
runs/m1828_executable_v2_stable_source_repaired_targeted_reset_feasibility_preflight/reset_stress_rows.csv
```

Metadata check:

| field | value |
| --- | ---: |
| repaired spec count | 36 |
| target failed AES profiles | 24 |
| target source count | 2 |

Target sources:

```text
m1771-bp1-00
m1771-bp1-02
```

## Output Directory

```text
runs/m1843_executable_v2_reset_time_aes_feasibility_scan
```

## Exact M1843 Command

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

This command scans:

```text
24 profiles * 120 distances * 61 half-widths = 175680 grid cells
```

It must not call `AutoDriftEnv.reset`, step the environment, or execute a policy
action. It only reproduces reset RNG state up to speed/mu/friction-step timing
and classifies deterministic obstacle grid cells.

## Expected Output Artifacts

```text
summary.json
reset_time_aes_feasibility_profile_summary.csv
reset_time_aes_feasibility_source_summary.csv
reset_time_aes_feasibility_accepted_cells.csv
reset_time_aes_feasibility_label_counts.csv
reset_time_aes_feasibility_reject_reason_counts.csv
reset_time_aes_feasibility_boundary_examples.csv
reset_time_aes_feasibility_claim_boundary.csv
```

## Expected Counts

M1843 should pass as an execution if:

| field | expected |
| --- | ---: |
| `target_source_count` | 2 |
| `target_profile_count_total` | 24 |
| `grid_cell_count_total` | 175680 |
| `expected_source_match` | true |
| `expected_profile_match` | true |
| `guardrail_violation_count` | 0 |
| `environment_reset_started` | false |
| `policy_action_executed` | false |

`result_class` can be one of:

```text
reset_time_aes_feasibility_scan_full_support
reset_time_aes_feasibility_scan_partial_support
reset_time_aes_feasibility_scan_no_support
```

The result class determines the M1844 audit route; it is not a controller
ranking or paper-level result.

## Follow-Up

If M1843 runs, route to:

```text
m1844-executable-v2-reset-time-aes-feasibility-scan-result-audit
```

M1844 should decide whether the scan supports:

- source repair v3 design using accepted-cell-derived ranges;
- partial-support audit and source/profile split;
- branch synthesis and task/source metadata pivot if no support is observed.

## Guardrails

- project artifact scan execution: `false`
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

- exact reset-time AES feasibility scan command and expected counts;
- M1843 scan execution is admitted.

Unsupported:

- scan result;
- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
