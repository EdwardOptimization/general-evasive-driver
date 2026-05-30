# M1800 Executable V2 Label-Source Compatibility Preflight

- status: completed
- decision: `label_source_compatibility_preflight_pass_route_to_result_audit`
- artifact: `runs/m1800_executable_v2_label_source_compatibility_preflight/summary.json`
- reset run: `false`
- rollout started: `false`
- training/replay/PPO: `false`

## Command

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

## Result

M1800 matched the pre-registered M1799 counts:

| field | value |
| --- | ---: |
| `input_spec_count` | 312 |
| `input_reset_row_count` | 312 |
| `compatible_spec_count` | 272 |
| `compatibility_violation_count` | 36 |
| `sparse_failure_count` | 4 |
| `unobserved_count` | 0 |
| `replacement_need_count` | 6 |
| `profile_control_count` | 12 |
| `role_surface_count` | 6 |
| `labels_enter_actor_input_count` | 0 |
| `ranking_admissible_by_default_count` | 0 |
| `guardrail_violation_count` | 0 |

Support-status group counts:

| support status | groups |
| --- | ---: |
| `supported_observed` | 20 |
| `unsupported_systematic` | 3 |
| `sparse_fragile` | 3 |

Compatible row counts by role surface:

| role surface | compatible rows |
| --- | ---: |
| `drift_required_recovery` | 36 |
| `hidden_robust_aes_feasible` | 32 |
| `hidden_robust_drift_required` | 72 |
| `hidden_robust_unavoidable_mitigation` | 60 |
| `stable_avoidance_aes` | 36 |
| `unavoidable_mitigation` | 36 |

Claim flags:

```text
compatible_reset_rerun_admissible: true
measured_execution_admissible: false
controller_family_ranking_admissible: false
```

## Artifact Set

M1800 wrote:

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

## Interpretation

M1800 gives a clean compatibility split:

- `272` rows are compatible for a later no-reset or reset-only subset route.
- `36` rows are systematic stable source-label violations and need alternate
  source materialization or source-label support repair.
- `4` rows are sparse hidden-robust AES failures and should be handled by a
  seed-fragility or tight-filter probe after the systematic stable repair.
- No rows are unobserved.

The compatible subset is not a comparison-ready benchmark. It is imbalanced
after quarantine: `stable_avoidance_aes` has `36` compatible rows, and
`hidden_robust_aes_feasible` has `32`. Measured execution and controller-family
ranking therefore remain blocked.

## Route Decision

Route to:

```text
m1801-executable-v2-label-source-compatibility-result-audit
```

M1801 should decide whether the next branch should:

- run a reset-only rerun on the compatible subset;
- materialize alternate stable source-label support first;
- probe sparse hidden-robust seed fragility;
- or repair the compatibility helper.

The current evidence suggests that source top-up/materialization is likely
needed before any measured execution or ranking route.

## Guardrails

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

- no-reset compatibility preflight result;
- source-label support and quarantine artifact materialization;
- compatible reset-rerun subset admission.

Unsupported:

- complete reset feasibility;
- measured execution;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
