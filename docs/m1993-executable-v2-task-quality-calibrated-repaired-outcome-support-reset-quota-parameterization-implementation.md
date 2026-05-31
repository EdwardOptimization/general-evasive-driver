# M1993 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Reset Quota Parameterization Implementation

- status: completed
- decision: `task_quality_calibrated_outcome_support_reset_quota_parameterization_implementation_pass_route_to_audit`
- implementation: `src/autodrift/executable_v2_task_quality_calibrated_reset_validation_preflight.py`
- focused tests: `4 passed`
- real M1990 reset rerun in M1993: `false`
- rollout/measured execution in M1993: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## What Changed

M1993 replaces the reset validator's active quota gate with artifact-driven
expectations derived from the input executable specs.

Before M1993:

```text
source_kind_quota_pass =
  observed_reset_source_kind_counts == EXPECTED_SOURCE_KIND_COUNTS

role_surface_quota_pass =
  observed_reset_role_surface_counts == EXPECTED_ROLE_SURFACE_COUNTS
```

The constants encoded the older M1956/M1958 panel and rejected M1986's repaired
outcome-support distribution.

After M1993:

```text
expected_source_kind_counts =
  count(spec.repair_source_kind for spec in executable_task_specs)

expected_role_surface_counts =
  count(spec.repair_source_kind,
        spec.source_role_semantics,
        spec.normalized_surface_variant
        for spec in executable_task_specs)

source_kind_quota_pass =
  observed_reset_source_kind_counts == expected_source_kind_counts

role_surface_quota_pass =
  observed_reset_role_surface_counts == expected_role_surface_counts
```

The validator still fails closed if required quota metadata is missing.

New summary fields:

```text
expected_quota_source: executable_task_specs
expected_source_kind_counts
expected_role_surface_counts
quota_metadata_missing_count
```

New artifact:

```text
quota_metadata_missing_rows.csv
```

Pass conditions now require:

```text
quota_metadata_missing_count == 0
source_kind_quota_pass == true
role_surface_quota_pass == true
```

## Tests

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_executable_v2_task_quality_calibrated_reset_validation_preflight.py
```

Result:

```text
4 passed
```

Covered behavior:

- contract rows preserve calibrated metadata;
- one real legacy spec still reset-validates under artifact-driven expected
  counts;
- a repaired M1986-style distribution with non-legacy quotas passes when reset
  rows match the active specs;
- missing quota metadata fails closed even when reset succeeds.

## Claim Boundary

M1993 supports only:

```text
focused reset-validator quota repair implementation and tests.
```

M1993 does not support:

- M1986 reset-validation pass under the repaired validator;
- measured rollout success;
- controller-family ranking;
- paper-level benchmark evidence;
- finite-window vs GRU comparison;
- level3 self-identification.

The real M1990 semantic rerun remains blocked until M1994 audits this
implementation.

## Next

Next milestone:

```text
m1994-executable-v2-task-quality-calibrated-repaired-outcome-support-reset-quota-parameterization-implementation-audit
```

M1994 should audit the implementation and decide whether a repaired reset
validation rerun command is admissible.
