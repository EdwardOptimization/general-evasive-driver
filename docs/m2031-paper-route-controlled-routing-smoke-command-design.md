# M2031 Paper-Route Controlled Routing Smoke Command Design

- status: completed
- decision: `controlled_routing_smoke_command_design_route_to_materialization_adapter_design`
- blocker source: `docs/m2030-paper-route-t2-t3-source-generation-preflight-result-audit.md`
- target panel source artifact: `runs/m2029_paper_route_t2_t3_source_generation_preflight/merged_panel_sources.csv`
- reset/rollout/measured execution in M2031: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2031 checks whether a bounded routing-smoke command can be frozen directly
over the M2029 projected-ready panel. The answer is no: the source panel is
ready at the coverage/provenance layer, but it is not yet materialized as
executable task specs plus a planned workload.

This is not a negative project result. It is a boundary decision:

```text
coverage-ready source panel
  != executable routing-smoke workload
```

## Runner Audit

Two existing runner paths were checked.

### Existing controller-family routing smoke

Relevant module:

```text
src/autodrift/controller_family_measured_routing_smoke.py
```

Why it is not the right command:

```text
It selects hard-coded decisive-history hook specs.
It is centered on T4/T5 routing families.
It does not consume M2029 merged_panel_sources.csv.
It would not preserve the newly generated T2/T3 source provenance.
It would not exercise the full projected-ready controlled panel.
```

Using this runner directly would be a shortcut: it would run a historical smoke,
not the M2029 panel.

### Existing calibrated measured runner

Relevant module:

```text
src/autodrift/executable_v2_task_quality_calibrated_measured_runner.py
```

Why it is not directly runnable yet:

```text
It expects executable_task_specs.json.
It expects planned_workload.csv.
It can preserve workload-derived quota metadata once those artifacts exist.
M2029 currently provides source rows and source specs, not executable env specs.
```

This runner is a plausible execution backend later, but M2032 must first
materialize the M2029 panel into compatible executable specs and workload rows.

## Command Decision

Decision:

```text
do_not_freeze_execution_command_yet
route_to_materialization_adapter_design
```

Rationale:

- A direct command would either ignore M2029 source provenance or fail schema
  expectations.
- The next highest-leverage step is a no-rollout adapter design that maps
  M2029 panel rows into executable task specs and planned workload rows.
- Execution remains blocked until that adapter route is designed, implemented,
  and audited.

## Routing-Smoke Scope For The Adapter

M2032 should design a bounded smoke workload, not a full benchmark.

Default scope to design:

```text
source selection:
  source-kind-balanced subset from all five families;
  include every generated T2/T3 source kind at least once;
  include T1/T4/T5 ready-family representatives;
  preserve panel_source_id, panel_task_family, source_kind, source_edge,
  source_role_semantics, parent_feasibility_tier_id,
  normalized_surface_variant, sampled_obstacle_label, and source_reference.

profile selection:
  all 12 registered controller profiles, to validate profile loading and
  observation/action contract routing.

episode target:
  bounded smoke size, not full ranking.
  M2032 should compute this from selected sources x 12 profiles.
```

If the adapter cannot produce executable specs for generated T2/T3 rows without
inventing simulator semantics, it must fail closed and route to generated-source
semantics repair rather than execution.

## Supported Claims

Supported:

```text
M2029 panel sources cannot be executed directly by the existing smoke runner
without losing provenance.
A materialization adapter design is required before routing smoke execution.
The calibrated measured runner is a possible backend after executable specs and
workload rows exist.
```

Unsupported:

```text
The M2029 panel has been reset-validated.
The M2029 panel has been rolled out.
The routing-smoke command is frozen.
Controller families can be ranked.
Finite-window-vs-GRU can be concluded.
Paper-level benchmark evidence exists.
Level3 self-identification evidence exists.
```

## Next Route

M2032 should design:

```text
paper-route controlled routing-smoke materialization adapter
```

The design must define:

```text
input artifacts;
source selection policy;
executable task spec schema;
planned workload schema;
profile metadata and checkpoint requirements;
quota/coverage preservation;
guardrails;
result classes;
claim boundary;
follow-up implementation artifact contract.
```

M2032 must not run environment reset, rollout, policy actions, measured
execution, training, replay, PPO, ranking, or paper/self-ID claims.
