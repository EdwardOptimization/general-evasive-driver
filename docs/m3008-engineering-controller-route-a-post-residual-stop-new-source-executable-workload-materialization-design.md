# M3008 Engineering Controller Route A Post-Residual-Stop New Source Executable Workload Materialization Design

## Metadata

- status: completed
- decision: `admit_m3009_new_source_executable_workload_materialization_preflight`
- manifest: `experiments/manifests/m3008-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-design.json`
- design artifact: `docs/m3008-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-design.md`
- parent audit: `docs/m3007-engineering-controller-route-a-post-residual-stop-new-task-source-generation-contract-materialization-result-audit.md`
- parent summary: `runs/m3006_engineering_controller_route_a_post_residual_stop_new_task_source_generation_contract_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m3009-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-preflight.json`
- next: `m3009-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-preflight`

M3008 is design-only. It does not materialize executable environment configs,
build sources, reset, step, rollout, replay, validate, train, rank, promote, or
claim repair success or performance.

## Design Decision

M3008 admits M3009 as a no-execution executable-workload materialization
preflight. The M3009 target is a bounded Route A engineering workload contract:

```text
source specs: 16 M3006 new task_source ids
profile bindings: 2 read-only engineering bindings
target workload rows: 32
execution scheduled by M3009: false
validation scheduled by M3009: false
training scheduled by M3009: false
```

The two profile bindings are:

```text
route_a_candidate_m2655_mitigation_preserving:
  checkpoint: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/checkpoints/m2655_mitigation_preserving_actor_head_repair.pt
  config lineage: runs/m2655_engineering_controller_route_a_source_only_gap_targeted_repair_mitigation_preserving_execution/repair_config_snapshot.json

route_a_parent_l3_online_gru:
  checkpoint: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/checkpoint.pt
  config lineage: runs/m1674_controller_family_one_seed_public_pilot/profile_runs/L3_online_gru/seed_167400/config.json
```

These are bindings only. M3009 may check path existence and actor contract
metadata, but it must not load checkpoints for action execution or mutate them.

## M3009 Required Artifacts

M3009 must write:

```text
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/summary.json
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/source_spec_resolution_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/profile_binding_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/executable_workload_contract_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/rejected_workload_shortcut_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/actor_contract_guard_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/claim_boundary_rows.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/gate_matrix.csv
runs/m3009_engineering_controller_route_a_post_residual_stop_new_source_executable_workload_materialization_preflight/run_state.json
docs/m3009-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-preflight.md
experiments/manifests/m3010-engineering-controller-route-a-post-residual-stop-new-source-executable-workload-materialization-result-audit.json
```

M3009 must fail or stop if it cannot preserve all 16 M3006 source identities,
if any workload row reuses an exhausted `m1680-spec-*` identity as the new
identity, if a profile binding is missing, or if it would need actor-visible
source/route/outcome/progress/verdict labels.

## Gate Contract

M3009 gates must include:

```text
M3007 audit doc exists
M3006 summary status_pass true
M3006 gate_matrix_pass true
16 M3006 source spec rows preserved
16 unique M3006 task_source ids
0 old M1690 L3 task_source-id overlap
2 read-only profile bindings
32 workload contract rows
all workload rows preserve actor observation 72 and action 3
no hidden/oracle/future-target/source/route/outcome/progress/verdict actor input
no source build execution validation training PPO ranking promotion or claims
M3010 result-audit manifest written
```

## Supported And Unsupported Claims

Supported M3008 claim:

```text
M3009 no-execution workload materialization is now precisely scoped.
```

Unsupported claims:

```text
executable workload materialized
source build readiness
environment execution readiness
execution result
validation result
repair success
driver performance
current-sim verdict
paper evidence
high-fidelity validation
finite-window-vs-GRU result
full ideal driver completion
level3 self-identification
checkpoint ranking or promotion
```

## Next

M3009 should implement the bounded no-execution materialization runner and
write the M3010 result-audit manifest. It must not execute the 32 workload rows
or interpret them as a result.
