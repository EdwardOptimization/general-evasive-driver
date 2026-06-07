# M3011 Engineering Controller Route A Post-Residual-Stop New Source Executable Env Materialization Design

## Metadata

- status: completed
- decision: `admit_m3012_new_source_executable_env_materialization_preflight`
- manifest: `experiments/manifests/m3011-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-design.json`
- design artifact: `docs/m3011-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-design.md`
- parent audit: `docs/m3010-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-result-audit.md`
- parent workload summary: `runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-preflight.json`
- next: `m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-preflight`

M3011 is design-only. It does not materialize env configs, build sources, reset,
step, rollout, validate, train, rank, promote, or claim repair success or
performance.

## Design Decision

M3011 admits M3012 as a no-execution executable env materialization preflight.
M3012 is the missing layer between M3009 workload-contract rows and any later
execution design.

Target materialization:

```text
source specs: 16 M3006 new task_source ids
profile bindings: 2 M3009 read-only bindings
workload rows: 32 M3009 workload contract rows
env config rows: 16 source-level env configs
executable workload rows: 32 workload rows joined to env configs
execution scheduled by M3012: false
validation scheduled by M3012: false
training scheduled by M3012: false
```

## Mapping Contract

M3012 should reuse the existing source-materialization semantics from
`controller_family_executable_workload_materialization_preflight.py`:

```text
choose the executable source endpoint by task-family match when possible
fall back only to supported public source families
use deterministic proxy env templates for proxy fault families
assert the human-view env contract for every env config
reject forbidden hidden/action/target/label keys
```

M3012 may create proxy env configs. A proxy env config is acceptable only as
materialization infrastructure; it is not proof that the new source is final
paper-quality or that execution will succeed.

## Required M3012 Artifacts

M3012 must write:

```text
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/summary.json
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_source_spec_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_source_specs.json
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/executable_workload_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/profile_binding_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/unmappable_source_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/env_contract_guard_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/actor_contract_guard_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/claim_boundary_rows.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/gate_matrix.csv
runs/m3012_engineering_controller_route_a_post_residual_stop_new_source_executable_env_materialization_preflight/run_state.json
docs/m3012-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-preflight.md
experiments/manifests/m3013-engineering-controller-route-a-post-residual-stop-new-source-executable-env-materialization-result-audit.json
```

## Gate Contract

M3012 must pass only if:

```text
M3010 audit doc exists
M3009 summary status_pass true
M3009 gate_matrix_pass true
16 M3006 source specs are materialized to env configs
16 unique M3006 source identities are preserved
0 old M1690 L3 source-id overlap remains true
0 unmappable source rows
0 env contract violations
0 forbidden key violations
2 read-only profile bindings are preserved
32 executable workload rows are materialized
actor observation 72 action 3 remains unchanged
no hidden/oracle/future-target/source/route/outcome/progress/verdict actor input
no reset step rollout replay validation training PPO ranking promotion or claim
M3013 result-audit manifest is written
```

## Supported And Unsupported Claims

Supported M3011 claim:

```text
M3012 no-execution executable env materialization is precisely scoped.
```

Unsupported claims:

```text
env configs materialized
execution readiness
closed-loop result
validation result
repair success
driver performance
paper evidence
high-fidelity validation
finite-window-vs-GRU result
full ideal driver completion
level3 self-identification
ranking or promotion
```

## Next

M3012 should implement the no-execution env materialization runner and register
M3013 result audit. It must not execute the 32 rows or interpret materialized
env configs as closed-loop evidence.
