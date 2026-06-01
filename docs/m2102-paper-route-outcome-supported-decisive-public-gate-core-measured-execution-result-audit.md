# M2102 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Result Audit

- status: completed
- decision: `public_gate_core_measured_execution_audit_route_to_metadata_and_sampling_repair_design`
- audited artifact: `runs/m2101_paper_route_outcome_supported_decisive_public_gate_core_measured_execution/summary.json`
- reset/rollout/measured execution in M2102: `false`
- policy actions executed in M2102: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Summary

M2101 is an incomplete measured-execution artifact:

```text
result_class: controlled_routing_smoke_measured_execution_incomplete_or_fail
episode_count: 478 / 480
failure_count: 2
metadata_missing_count: 480
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

The run did execute rollout and policy actions, but it is not complete and must
not be used for controller-family ranking or paper-level claims.

## Blocker 1: Scenario Sampling Failure

Two workload cells failed:

```text
m2063-osd-osd_v0_0162_t3::L2_window_50
m2063-osd-osd_v0_0235_t5::L3_online_gru
```

Both failed with:

```text
failed to sample an obstacle scenario matching the configured filters
```

This is a measured-run sampling blocker, not a policy-performance result.

## Blocker 2: Full Metadata Completeness

All 480 workload rows are missing the same full metadata fields:

```text
source_role_semantics
parent_feasibility_tier_id
normalized_surface_variant
sampled_obstacle_label
```

M2098 repaired the fields required for pre-rollout validation, but the measured
runner's final metadata completeness audit is stricter and still requires these
controlled-routing metadata fields.

The likely repair direction is metadata-only:

```text
source_role_semantics := spec.task_role_semantics
parent_feasibility_tier_id := tier_not_applicable_outcome_supported_decisive
normalized_surface_variant := spec.window_tag or source_origin-derived sentinel
sampled_obstacle_label := label_not_applicable_generated_proxy
```

The exact mapping must be designed before implementation.

## Decision

Do not rerun measured execution yet.

M2102 routes to a combined repair design:

```text
metadata completeness repair for all 480 workload rows
targeted scenario-sampling repair for the two failing workload cells/specs
no env_config mutation unless explicitly designed and audited
no weakening measured-runner validation
no ranking or paper claims
```

## Supported Claims

Supported:

```text
M2101 produced a partial measured execution artifact with 478 completed cells.
The active blockers are two scenario-sampling failures and full metadata
completeness, with metric completeness and guardrail clean.
```

Unsupported:

```text
complete measured execution;
controller-family ranking;
paper-level benchmark evidence;
finite-window-vs-GRU conclusion;
level3 self-identification.
```

## Next

Next milestone:

```text
m2103-paper-route-outcome-supported-decisive-public-gate-core-measured-execution-repair-design
```
