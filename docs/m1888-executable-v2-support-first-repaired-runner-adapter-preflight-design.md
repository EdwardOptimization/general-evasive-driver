# M1888 Executable V2 Support-First Repaired Runner Adapter Preflight Design

- status: completed
- decision: `support_first_repaired_adapter_preflight_design_admit_preflight_run`
- parent implementation: `src/autodrift/executable_v2_support_first_repaired_runner_adapter.py`
- preflight execution run in M1888: false
- reset/rollout in M1888: false
- training/replay/PPO: false

## Summary

M1888 registers the exact no-rollout command for running the repaired runner
adapter on real M1884/M1875/M1880 artifacts. It does not run the command.

The preflight target remains bounded smoke, not full matrix execution:

```text
sources per role surface: 2
role surfaces: 8
controller profiles: 12
selected source specs: 16
patched executable specs: 48
new geometry rollout workload cells: 576
import rows: 384
total repaired smoke panel rows: 960
```

## Exact Command

```bash
PYTHONPATH=src python -m autodrift.executable_v2_support_first_repaired_runner_adapter \
  --repair-matrix runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv \
  --measured-specs runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json \
  --episode-rows runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv \
  --output-dir runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight \
  --sources-per-role-surface 2 \
  --target-role-surface-count 8 \
  --target-controller-profile-count 12 \
  --target-selected-source-spec-count 16 \
  --target-executable-spec-count 48 \
  --target-rollout-workload-cell-count 576 \
  --target-import-row-count 384 \
  --target-total-panel-row-count 960 \
  --next-blocker m1890-executable-v2-support-first-repaired-runner-adapter-preflight-result-audit
```

## Expected Artifacts

```text
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/summary.json
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.json
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_executable_specs.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_workload_matrix.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_import_rows.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_selection.csv
runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/repaired_measured_claim_boundary.csv
```

## Pass Gates

The M1889 preflight should pass only if:

- result class is `support_first_repaired_runner_adapter_pass`;
- selected source spec count is `16`;
- role-surface count is `8`;
- controller profile count is `12`;
- executable spec count is `48`;
- rollout workload cell count is `576`;
- import row count is `384`;
- total panel row count is `960`;
- config failure count is `0`;
- missing import row count is `0`;
- duplicate spec/workload counts are `0`;
- profile alias mismatch count is `0`;
- guardrail violation count is `0`;
- environment reset, environment rollout, policy action execution, training,
  replay, PPO, private holdout, ranking, paper claims, and level3 self-ID
  claims all remain false.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- preflight execution started in M1888: `false`
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

- the exact no-rollout real-artifact preflight command is registered;
- M1889 may run the adapter preflight;
- repaired measured execution and ranking remain blocked.

Unsupported:

- real preflight result;
- repaired measured execution result;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1889 no-rollout repaired adapter preflight execution. Do not run
environment reset, environment rollout, measured execution, training, replay,
PPO, ranking, paper claims, or level3 self-ID claims.
