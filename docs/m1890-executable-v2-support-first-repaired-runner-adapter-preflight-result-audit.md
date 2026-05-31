# M1890 Executable V2 Support-First Repaired Runner Adapter Preflight Result Audit

- status: completed
- decision: `support_first_repaired_adapter_preflight_audit_admit_bounded_smoke_execution_design`
- audited summary: `runs/m1889_executable_v2_support_first_repaired_runner_adapter_preflight/summary.json`
- reset/rollout in M1890: false
- measured execution: false
- training/replay/PPO: false

## Summary

M1890 audits M1889 as a clean no-rollout preflight result. The preflight is
complete enough to admit repaired bounded-smoke execution design, but it does
not admit direct execution.

Audited facts:

```text
result_class: support_first_repaired_runner_adapter_pass
selected_source_spec_count: 16 / 16
role_surface_count: 8 / 8
controller_profile_count: 12 / 12
executable_spec_count: 48 / 48
rollout_workload_cell_count: 576 / 576
import_row_count: 384 / 384
total_panel_row_count: 960 / 960
config_failure_count: 0
missing_import_row_count: 0
duplicate_spec_count: 0
duplicate_workload_count: 0
profile_alias_mismatch_count: 0
guardrail_violation_count: 0
```

The artifacts preserve the original distinction:

```text
new rollout rows:
  finish_extended: 192
  road_relaxed: 192
  road_relaxed_finish_extended: 192

import/postprocess rows:
  original: 192
  semantics_only: 192
```

## Execution-Readiness Audit

M1889 is ready for execution design, not direct execution.

Reason:

- the existing support-first measured runner expects
  `support_first_measured_executable_specs`;
- M1889 emits `support_first_repaired_measured_executable_specs`;
- M1889 also emits import rows that should be merged with rollout rows after
  execution;
- repaired episode rows must preserve repair variant metadata and support
  post-execution aggregates by repair variant;
- direct use of the old runner would omit import-row semantics and repaired
  aggregate outputs.

Therefore, the next step should design a repaired bounded-smoke execution
wrapper/protocol before any rollout.

## Next Route

Admit:

```text
m1891-executable-v2-support-first-repaired-bounded-smoke-execution-design
```

M1891 should design:

- how to feed `support_first_repaired_measured_executable_specs` into a runner;
- how to run only the `576` geometry workload rows;
- how to merge `384` import rows after rollout;
- how to preserve repair variant metadata in episode rows;
- which aggregates are required for M1890-style post-execution audit;
- exact pass/fail gates before any controller-family ranking.

Do not admit direct repaired measured execution from M1890.

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

- M1889 no-rollout preflight is count-complete and guardrail-clean;
- repaired bounded-smoke execution design is admissible;
- direct rollout remains blocked until wrapper/protocol design.

Unsupported:

- repaired measured execution result;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1891 repaired bounded-smoke execution design. Keep direct measured
execution, controller-family ranking, paper-level claims, and level3 self-ID
claims blocked.
