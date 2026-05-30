# M1751 Paper-Route Task-Quality Revised Scenario Taxonomy Execution Adapter Result Audit

- status: completed
- decision: `adapter_audit_admit_revised_execution_design`
- audited milestone: `docs/m1750-paper-route-task-quality-revised-scenario-taxonomy-execution-adapter-implementation.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1751 audits M1750 as a clean revised-execution adapter implementation. The
adapter preserves M1743 outcome semantics, separates metadata specs from
executable scenario specs, writes semantics-aware aggregates, and adds
applicability-aware metric completeness reports.

The audit admits a revised measured-execution design milestone. It does not
admit immediate rollout or any controller-family ranking.

## Audit Findings

### Semantics Loading

`load_scenario_specs` now accepts all three payload forms used by this branch:

```text
scenario_specs
repaired_scenario_specs
semantics_scenario_specs
```

This keeps old scenario-taxonomy paths compatible while allowing M1743
semantics materialization artifacts to be used by the revised runner.

### Semantics Pass-Through

The workload and episode/failure rows preserve `16` M1743 semantics fields:

```text
evaluation_role
primary_metric_family
ranking_eligible_after_audit
diagnostic_only_no_ranking_claim
benchmark_row
metric_required_*
```

This closes the M1749 blocker where the runner could compute outcome metrics
but would drop the semantics needed to interpret them.

### Metadata And Executable Specs

The runner now supports a separate `--executable-scenario-specs` path. This is
required because M1743 semantics specs are metadata, while M1734 repaired specs
contain executable `env_config` payloads.

The revised execution should therefore use:

```text
--scenario-specs runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_specs.json
--workload runs/m1743_task_quality_outcome_semantics_materialization_preflight/semantics_scenario_matrix.csv
--executable-scenario-specs runs/m1734_task_quality_scenario_taxonomy_sampling_repair_preflight/repaired_scenario_specs.json
```

### Metric Completeness

M1750 adds explicit completeness outputs:

```text
metric_completeness_summary.csv
metric_completeness_failures.csv
```

The applicability rules are correct for revised execution:

- pass-time fields are finite when `obstacle_passed_raw == true`;
- recovery-time fields are finite when `recovery_success == true`;
- impact fields are finite when `collision == true`;
- no-recovery after obstacle pass is an outcome, not a logging failure.

### Aggregate Hooks

M1750 adds:

```text
evaluation_role_aggregate.csv
primary_metric_family_aggregate.csv
evaluation_role_outcome_aggregate.csv
primary_metric_family_outcome_aggregate.csv
```

These are required before any later audit can separate benchmark,
diagnostic-stress, and mitigation-diagnostic rows.

## Verification

M1750 verification:

```text
focused scenario-taxonomy tests: 10 passed
affected execution/metric tests: 21 passed
full test suite: 1707 passed, 4 warnings
compileall: passed
research validation: passed
```

M1751 did not run a full environment rollout.

## Guardrails

- full rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1750 is a clean adapter implementation;
- semantics pass-through is implemented and tested;
- metric completeness helpers are implemented and tested;
- revised execution design is now admissible.

Unsupported:

- revised rollout result;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to M1752 adapter-aware revised scenario taxonomy measured-execution
design. The design must pre-register exact inputs, output directory, seed base,
required artifacts, completeness gates, and no-ranking/no-paper-claim
boundaries before any rollout.
