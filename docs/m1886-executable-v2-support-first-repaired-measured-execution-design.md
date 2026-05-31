# M1886 Executable V2 Support-First Repaired Measured Execution Design

- status: completed
- decision: `support_first_repaired_measured_execution_design_admit_adapter_implementation`
- parent audit: `docs/m1885-executable-v2-support-first-success-semantics-task-quality-repair-materialization-result-audit.md`
- repair matrix: `runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv`
- reset/rollout in M1886: false
- training/replay/PPO: false

## Summary

M1886 designs the repaired measured execution route after M1884/M1885. The
materialized `10800`-row matrix is complete, but it is not directly consumable
by the existing support-first runner because repair variants are represented as
`config_delta_json` metadata rather than patched executable specs.

Decision:

```text
Do not run the full 10800-cell matrix directly.
First implement a no-rollout repaired runner adapter.
Then run a bounded repaired smoke before any full-matrix execution.
```

## Variant Execution Policy

The five M1884 repair variants have different execution semantics:

```text
original:
  no new rollout required for first repaired smoke;
  import M1880 rows as baseline evidence for the same selected sources.

semantics_only:
  no new rollout required;
  recompute role-aware diagnostic semantics from existing M1880 metrics.

finish_extended:
  new rollout required;
  apply max_steps / post-obstacle recovery-window delta.

road_relaxed:
  new rollout required;
  apply road-boundary relaxation delta.

road_relaxed_finish_extended:
  new rollout required;
  apply both geometry deltas.
```

This keeps the protocol honest: metric semantics are postprocessing outputs,
while geometry variants are actual environment changes. Neither path changes
the actor observation schema, controller profile, checkpoint, or reward shortcut
into actor input.

## Adapter Requirements

The next helper must consume:

```text
runs/m1884_executable_v2_support_first_success_semantics_task_quality_repair_materialization/repair_variant_matrix.csv
runs/m1875_executable_v2_support_first_measured_runner_adapter_preflight/support_first_measured_executable_specs.json
runs/m1880_executable_v2_support_first_measured_runner_execution/episode_rows.csv
```

It must emit no-rollout artifacts:

```text
repaired_measured_executable_specs.json
repaired_measured_executable_specs.csv
repaired_measured_workload_matrix.csv
repaired_measured_import_rows.csv
repaired_measured_selection.csv
repaired_measured_claim_boundary.csv
summary.json
```

Required invariants:

- every emitted rollout workload row has exactly one controller profile;
- controller profile config and checkpoint paths are copied unchanged;
- original baseline rows are retained as import rows, not dropped;
- semantics-only rows are import/postprocessing rows, not new rollouts;
- geometry variants become patched executable specs with unique repair IDs;
- repair metadata survives into workload rows and later episode rows;
- semantic labels and outcomes remain metric outputs only;
- actor input contract remains unchanged.

## Config Delta Mapping

The adapter must map M1884 `config_delta_json` into concrete executable specs.
The mapping must be explicit and validated with `build_env_config`.

Required initial mapping:

```text
success_semantics:
  no env_config change;
  write success_semantics_variant_id and role_semantics_id only.

max_steps_multiplier:
  patched_env_config.max_steps =
    ceil(base_env_config.max_steps_or_default * multiplier)

track_width_multiplier:
  patched_env_config.track_width =
    base_env_config.track_width_or_default * multiplier

offtrack_overshoot_tolerance_m:
  metric metadata only for repaired audit;
  no actor input or reward shortcut.

finish_rule:
  protocol metadata first;
  if later implemented as env change, it must modify only obstacle finish /
  recovery-window config and must be audited separately.
```

Unknown delta keys must fail preflight. This prevents silent task changes.

## Bounded Smoke Route

M1886 chooses bounded smoke before full matrix execution.

Smoke selection:

```text
2 source specs per role surface
8 role surfaces
12 controller profiles
3 rollout geometry variants
```

Expected new rollout workload:

```text
2 * 8 * 12 * 3 = 576 rollout cells
```

Expected imported diagnostic rows:

```text
2 * 8 * 12 * 2 = 384 imported rows
```

Expected total repaired smoke panel:

```text
960 rows
```

The selector should prefer source diversity within each role surface by using
distinct hidden-dynamics, road-boundary, timing, and lateral-offset buckets when
available. It should keep all `12` controller profiles. This smoke validates
runner plumbing and task semantics without turning one large execution into a
new unreviewed benchmark.

## Full Matrix Route

Full execution remains the follow-up route if the bounded smoke passes its
post-execution audit.

Full geometry rollout workload:

```text
180 support-first specs * 12 controller profiles * 3 geometry variants = 6480
```

Full imported baseline/semantics rows:

```text
180 support-first specs * 12 controller profiles * 2 import variants = 4320
```

Full repaired panel:

```text
10800 rows
```

No full matrix run should start before bounded smoke execution and post-smoke
audit confirm that patched configs, semantic recomputation, import alignment,
and aggregate outputs are correct.

## Required Post-Execution Outputs

The repaired runner must preserve enough metadata for audit before any ranking:

```text
repair_variant_aggregate.csv
repair_variant_role_panel_aggregate.csv
repair_variant_role_surface_aggregate.csv
repair_variant_controller_profile_aggregate.csv
repair_variant_outcome_aggregate.csv
role_semantics_diagnostic_aggregate.csv
import_vs_rollout_alignment.csv
metric_completeness_summary.csv
metric_completeness_failures.csv
```

Post-execution audit must decide whether the result is still task-quality
diagnostic, whether a full matrix is admissible, and only later whether ranking
can be considered. M1886 does not admit ranking.

## Next Step

Admit:

```text
m1887-executable-v2-support-first-repaired-runner-adapter-implementation
```

M1887 should implement the no-rollout adapter and focused tests only. It should
not run the real M1884 matrix. A later preflight milestone should run the helper
over the real artifacts and verify the expected `576/384/960` smoke counts.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
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

- repaired measured execution requires a new adapter/protocol;
- bounded smoke is the next measured route before full matrix execution;
- M1887 may implement the no-rollout adapter.

Unsupported:

- repaired measured execution result;
- controller-family ranking;
- policy improvement claim;
- paper-level benchmark result;
- level3 self-identification evidence.

## Decision

Route to M1887 repaired runner adapter implementation. Keep direct rollout,
full matrix execution, controller-family ranking, paper-level claims, and
level3 self-ID claims blocked.
