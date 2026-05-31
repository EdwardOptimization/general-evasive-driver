# M1984 Executable V2 Task-Quality Calibrated Repaired Outcome-Support Source-Mining Result Audit

- status: completed
- decision: `task_quality_calibrated_outcome_support_source_mining_audit_admit_materialization_design`
- audited summary: `runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/summary.json`
- source-mining rerun in M1984: `false`
- reset/rollout/measured execution in M1984: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Audit Result

M1983 is a clean no-rollout source-mining pass:

```text
result_class: task_quality_calibrated_outcome_support_source_mining_pass
input_template_count: 192
source_candidate_count: 192
resolution_failure_count: 0
accepted_cell_count_total: 8358
supported_source_count: 184
public_gate_supported_source_count: 73
unsupported_source_count: 8
guardrail_violation_count: 0
```

Repair-axis counts match the M1980/M1982 design:

```text
offtrack_anchor_relief: 64
offtrack_boundary_relief_extension: 32
success_support_expansion: 48
collision_mitigation_relief: 32
mitigation_metric_isolation: 16
```

Repair-axis support passes all floors:

```text
offtrack_anchor_relief: 64 / 64 supported
offtrack_boundary_relief_extension: 32 / 32 supported
success_support_expansion: 43 / 48 supported
collision_mitigation_relief: 29 / 32 supported
mitigation_metric_isolation: 16 / 16 supported
```

This is enough to admit bounded materialization design. It is not enough to
claim reset validity, measured rollout success, controller-family ranking, or
paper-level benchmark evidence.

## Unsupported Row Classification

M1983 has `8` unsupported rows:

```text
success_support_expansion: 5
collision_mitigation_relief: 3
```

Failure reasons:

```text
label_role_mismatch: 6
friction_timing_filter_only: 2
```

Source split:

```text
public_gate: 7
public_debug: 1
```

Interpretation:

- the unsupported success-support rows are exact-geometry rows whose local scan
  no longer contains the requested role label;
- the unsupported collision-mitigation rows are localized to one role mismatch
  and two post-friction-step timing-filter rows;
- none of the unsupported rows are needed to satisfy the M1982 support floors;
- they should be excluded from the first materialization subset and retained as
  diagnostics for possible later source repair.

The unsupported rows do not justify lowering support floors, rerunning source
mining, or moving directly to measured execution.

## Materialization Readiness

M1984 admits materialization design under these constraints:

```text
source input:
  use M1983 outcome_support_source_rows.csv and outcome_support_accepted_cells.csv
  select only source_support_status == supported
  exclude the 8 unsupported rows

claim boundary:
  materialization design only
  no reset validation
  no measured execution
  no controller ranking
  no paper-level claim
  no level3 self-ID claim

holdout:
  no private holdout is used in this repair branch

diagnostics:
  mitigation_metric_isolation rows may be carried as diagnostic-only rows
  do not treat them as obstacle-pass ranking rows
```

M1985 should design a bounded subset rather than materializing every accepted
cell. A reasonable starting point is:

```text
target selected sources: 80
target controller profiles per source: 12
target planned workload cells: 960

candidate source quota sketch:
  offtrack_anchor_relief: 24
  offtrack_boundary_relief_extension: 16
  success_support_expansion: 20
  collision_mitigation_relief: 12
  mitigation_metric_isolation: 8 diagnostic-only
```

M1985 may adjust the exact quota design, but it must preserve the audit
constraints: supported rows only, no unsupported rows, no holdout, no ranking
claim, and no profile-specific tuning.

## Supported Claims

M1984 supports:

- M1983 source mining passed with clean guardrails;
- the outcome-support repair branch has enough no-rollout source support for a
  bounded materialization design;
- offtrack-only blocker repair is strong at source-mining level;
- the remaining unsupported rows are localized and not required for the first
  materialization subset.

M1984 does not support:

- materialized executable specs;
- reset validity;
- measured rollout success;
- controller-family ranking;
- finite-window vs GRU conclusion;
- policy improvement;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Decision:

```text
admit_materialization_design
```

Rejected routes:

```text
direct materialization:
  rejected because subset quotas and representative-cell rules have not been
  designed.

source repair before materialization:
  rejected for now because support floors pass and the 8 unsupported rows can be
  excluded from the first bounded subset.

measured execution:
  rejected because no new materialized/reset-valid panel exists yet.

controller ranking:
  rejected because source mining is not controller evidence.
```

## Next

Next milestone:

```text
m1985-executable-v2-task-quality-calibrated-repaired-outcome-support-materialization-design
```

M1985 should design the bounded materialization subset before implementation.
