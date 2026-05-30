# M1799 Executable V2 Label-Source Compatibility Preflight Execution Design

- status: completed
- decision: `label_source_compatibility_execution_design_admit_preflight_run`
- source helper: `src/autodrift/executable_v2_label_source_compatibility_preflight.py`
- execution in this milestone: `false`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Exact Command

M1800 should run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.executable_v2_label_source_compatibility_preflight \
  --executable-v2-panel-specs runs/m1790_executable_v2_panel_spec_materialization_preflight/executable_v2_panel_specs.json \
  --reset-rows runs/m1794_executable_v2_reset_feasibility_preflight/reset_stress_rows.csv \
  --output-dir runs/m1800_executable_v2_label_source_compatibility_preflight \
  --target-input-spec-count 312 \
  --target-profile-count 12 \
  --next-blocker m1801-executable-v2-label-source-compatibility-result-audit
```

This command is no-reset and no-rollout. It only reads M1790 executable specs and
M1794 reset result rows.

## Input Artifacts

Required inputs:

```text
runs/m1790_executable_v2_panel_spec_materialization_preflight/executable_v2_panel_specs.json
runs/m1794_executable_v2_reset_feasibility_preflight/reset_stress_rows.csv
```

Expected output directory:

```text
runs/m1800_executable_v2_label_source_compatibility_preflight
```

Expected artifacts:

```text
summary.json
source_label_support.csv
compatibility_violation_rows.csv
sparse_failure_rows.csv
unobserved_rows.csv
replacement_need_rows.csv
compatible_executable_v2_panel_specs.json
compatible_executable_v2_panel_specs.csv
compatible_executable_v2_panel_matrix.csv
claim_boundary.csv
```

## Expected Counts

Pre-registered expected counts from M1794 rows:

| field | expected |
| --- | ---: |
| `input_spec_count` | 312 |
| `input_reset_row_count` | 312 |
| `compatible_spec_count` | 272 |
| `compatibility_violation_count` | 36 |
| `sparse_failure_count` | 4 |
| `replacement_need_count` | 6 |
| `profile_control_count` | 12 |
| `role_surface_count` | 6 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

Expected support-status group counts:

| support status | groups |
| --- | ---: |
| `supported_observed` | 20 |
| `unsupported_systematic` | 3 |
| `sparse_fragile` | 3 |

Expected claim-admission flags:

```text
compatible_reset_rerun_admissible: true
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Pass Criteria

M1800 should pass if:

- the command completes with `result_class=executable_v2_label_source_compatibility_preflight_pass`;
- all expected counts match;
- all expected artifacts exist;
- no reset, rollout, policy action, training, replay, PPO, private holdout,
  promotion, actor-input change, profile tuning, ranking, paper-level, or level3
  claim occurs;
- the next blocker is `m1801-executable-v2-label-source-compatibility-result-audit`.

M1800 should not attempt to repair source balance or run reset. Its job is only
to materialize compatibility evidence and quarantine rows.

## Route Decision

Route to:

```text
m1800-executable-v2-label-source-compatibility-preflight
```

M1800 executes the exact command above. M1801 should then audit whether the
compatible subset, systematic violations, and sparse failures imply a reset-rerun
subset, source top-up branch, seed-fragility probe, or design repair.

## Guardrails

- compatibility preflight executed in M1799: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
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

- exact no-reset compatibility execution design;
- pre-registered expected counts for M1800.

Unsupported:

- compatibility execution result;
- reset feasibility pass;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
