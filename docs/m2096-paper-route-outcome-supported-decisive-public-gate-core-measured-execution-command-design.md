# M2096 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Command Design

- status: completed
- decision: `public_gate_core_measured_command_design_route_to_metadata_compatibility_repair`
- manifest: `experiments/manifests/m2096-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-command-design.json`
- parent audit: `docs/m2095-paper-route-outcome-supported-decisive-public-gate-core-panel-extraction-result-audit.md`
- executable specs: `runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_executable_task_specs.json`
- planned workload: `runs/m2094_paper_route_outcome_supported_decisive_public_gate_core_panel_extraction/public_gate_core_planned_sentinel_workload.csv`
- measured execution in M2096: `false`
- rollout/policy actions in M2096: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Design Goal

M2096 was intended to freeze an exact measured-execution command for the M2094
public-gate core panel:

```text
executable task specs: 96
controller profiles: 5
planned workload rows: 480
device: cpu
```

Before freezing the command, M2096 audits runner compatibility without running
rollout or policy actions.

## Runner Compatibility Audit

Candidate runner:

```text
autodrift.paper_route_controlled_routing_smoke_measured_runner
```

The candidate runner is not directly compatible with the M2094 artifacts yet.

Required spec field missing:

```text
panel_source_id
```

Required workload fields missing:

```text
proxy_template_family
generated_source_row
```

The M2094 specs contain enough source metadata to repair these fields without
changing the task semantics or env configs:

```text
proxy_template_family exists in specs
generated_source_row exists in specs
task_source_id/source_reference/source_edge exist in specs
```

The planned workload was produced by a generic sentinel workload helper that
does not carry all controlled-routing-smoke runner metadata. This is a metadata
compatibility gap, not evidence that the public-gate panel is invalid.

## Decision

M2096 does not freeze a measured-execution run command.

Instead it routes to a no-rollout metadata compatibility repair design. The
repair should enrich specs/workload rows for the measured runner while obeying:

```text
do not change env_config
do not change scenario filters
do not resample tasks
do not run reset
do not run rollout or policy actions
do not rank controller families
do not make paper-level or self-ID claims
```

The intended repair direction is:

```text
spec.panel_source_id := existing task/source identifier from the same spec
workload.proxy_template_family := joined spec.proxy_template_family
workload.generated_source_row := joined spec.generated_source_row
```

The exact mapping must be frozen in the next milestone before implementation.

## Supported Claims

Supported:

```text
The M2094 public-gate core panel is not directly runnable by the existing
controlled-routing-smoke measured runner because metadata fields are missing.
The blocker is localized to metadata compatibility.
```

Unsupported:

```text
measured execution readiness;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2097-paper-route-outcome-supported-decisive-public-gate-core-measured-runner-compatibility-repair-design
```
