# M1968 Executable V2 Task-Quality Calibrated Offtrack Parent-Tier Normalization Design

- status: completed
- decision: `task_quality_calibrated_offtrack_parent_tier_normalization_design_admit_implementation`
- branch: `paper_route_task_quality_calibrated_materialization`
- reset/rollout/measured execution in M1968: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1966 failed closed before rollout because `parent_feasibility_tier_id` was
blank for the selected offtrack-boundary-relief sources.

M1967 localized the path:

```text
M1952 supported source rows with blank parent_feasibility_tier_id: 11
blank repair_source_kind: offtrack_boundary_relief
M1956 selected blank offtrack sources: 8
M1958 executable specs with blank parent_feasibility_tier_id: 8
M1958 planned workload rows with blank parent_feasibility_tier_id: 96
M1966 validation failure rows: 8 unique task sources
```

This is a metadata normalization gap, not a measured driver-performance result.

## Design Decision

Do not weaken measured-runner validation. `parent_feasibility_tier_id` remains a
required non-empty metadata field for calibrated measured execution.

Instead, M1969 should normalize blank offtrack-boundary-relief parent-tier
metadata to an explicit sentinel:

```text
tier_not_applicable_offtrack_boundary_relief
```

Semantics:

```text
The source belongs to the offtrack-boundary-relief repair axis and therefore has
no original parent feasibility tier. The value is intentionally normalized, not
unknown, and not suitable for feasibility-tier ranking.
```

Allowed normalization:

```text
if repair_source_kind == offtrack_boundary_relief
and parent_feasibility_tier_id is blank:
    parent_feasibility_tier_id = tier_not_applicable_offtrack_boundary_relief
```

Forbidden normalization:

```text
blank parent_feasibility_tier_id for any other repair_source_kind
blank repair_source_kind
blank source_role_semantics
blank normalized_surface_variant
```

Those cases should remain fail-closed.

## Implementation Route

M1969 should update:

```text
src/autodrift/executable_v2_task_quality_calibrated_materialization_preflight.py
tests/test_executable_v2_task_quality_calibrated_materialization_preflight.py
```

Implementation requirements:

- add a named sentinel constant;
- add a small helper that normalizes only the offtrack-boundary-relief blank
  case;
- use the helper when materializing executable specs;
- propagate the normalized value into `executable_task_specs.json`,
  `executable_task_specs.csv`, and `planned_workload.csv`;
- add summary counters for blank/normalized parent-tier metadata if practical;
- do not change actor inputs, env configs, controller profiles, or runner
  validation.

Focused tests should cover:

- offtrack-boundary-relief blank parent tier normalizes to the sentinel;
- non-offtrack blank parent tier is not silently normalized;
- planned workload rows inherit the normalized sentinel;
- the existing 80-spec / 960-workload synthetic preflight still passes.

## Validation Route

M1969 should run no environment reset and no measured rollout.

Expected command after implementation:

```bash
PYTHONPATH=src python -m autodrift.executable_v2_task_quality_calibrated_materialization_preflight \
  --subset-config configs/executable_v2_task_quality_calibrated_materialization_subset_v0.json \
  --repair-accepted-cells runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_accepted_cells.csv \
  --profile-run-dir runs/m1674_controller_family_one_seed_public_pilot \
  --output-dir runs/m1969_executable_v2_task_quality_calibrated_materialization_preflight_repaired \
  --next-blocker m1970-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-result-audit
```

Pass gates:

```text
result_class == task_quality_calibrated_materialization_preflight_pass
executable_task_spec_count == 80
planned_workload_cell_count == 960
blank parent_feasibility_tier_id count == 0
normalized offtrack sentinel count == 8 specs / 96 workload cells
contract_violation_count == 0
forbidden_key_violation_count == 0
guardrail_violation_count == 0
environment_reset_started == false
environment_rollout_started == false
measured_rollout_started == false
controller_family_ranking_claim_made == false
paper_level_claim_made == false
level3_self_id_claim_made == false
```

M1969 should not rerun measured execution. A repaired materialization result
must be audited before reset validation or measured execution is admitted again.

## Claim Boundary

If M1969 passes, it may claim only:

```text
The calibrated no-reset materialization artifacts no longer contain blank
offtrack-boundary-relief parent-tier metadata.
```

It still cannot claim measured rollout success, controller-family ranking,
paper-level benchmark evidence, policy improvement, finite-window-vs-GRU
comparison, or level3 self-identification.

## Next

Next milestone:

```text
m1969-executable-v2-task-quality-calibrated-offtrack-parent-tier-normalization-implementation
```

M1969 may implement the normalization and rerun no-reset materialization only.
