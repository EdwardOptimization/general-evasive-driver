# M1844 Executable V2 Reset-Time AES Feasibility Scan Result Audit

- status: completed
- decision: `reset_time_aes_no_support_audit_route_to_branch_synthesis`
- branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- parent result: `runs/m1843_executable_v2_reset_time_aes_feasibility_scan/summary.json`
- additional scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Audit Summary

M1843 completed the pre-registered no-reset scan:

```text
result_class: reset_time_aes_feasibility_scan_no_support
target_source_count: 2
target_profile_count_total: 24
grid_cell_count_total: 175680
accepted_cell_count_total: 0
guardrail_violation_count: 0
```

The count guardrails match M1842:

```text
expected_source_match: true
expected_profile_match: true
environment_reset_started: false
policy_action_executed: false
```

## Failure Classification

Primary classification:

```text
source_task_support_absence_for_stable_aes_only
```

Reason:

- no target profile has an accepted `aes_feasible` cell;
- no target source has support;
- the scan found non-AEB regions, but they were `drift_required` or
  `unavoidable`, not stable AES;
- reject reasons are limited to `aeb_feasible_rejected` and
  `label_not_allowed`;
- there is no evidence that threshold or friction-timing filters hid valid
  `aes_feasible` cells.

Observed labels:

| label | count |
| --- | ---: |
| `aeb_feasible` | 159820 |
| `drift_required` | 284 |
| `unavoidable` | 15576 |

Reject reasons:

| reject reason | count |
| --- | ---: |
| `aeb_feasible_rejected` | 159820 |
| `label_not_allowed` | 15860 |

Secondary artifact classification:

```text
claim_boundary_context_wording_artifact
```

The M1843 scan artifact includes a claim-boundary CSV emitted by the M1841
helper with wording that still says `project_artifact_scan_result` is
inadmissible because M1841 was implementation-only. That wording is stale for
M1843, where project artifact scan execution was explicitly admitted by M1842.
This is a claim-boundary wording artifact, not a scan-count artifact. The
summary fields and output tables support the no-support conclusion.

## Falsified Claims

Falsified for the current source-repair route:

- Static source candidate widening is enough to recover reset-time AES-only
  support.
- The selected M1825/M1828 failed AES rows contain stable AES-only obstacle
  support somewhere in `[1.0, 60.0] x [0.2, 1.4]`.
- Source repair v3 can be derived from accepted AES-only cells in the M1843
  scan.

Not falsified:

- The broader project goal.
- Drift-required or unavoidable scenario support.
- Future task/source metadata redesign that chooses sources with real stable
  AES-only reset-time support.
- Future executable-v2 panels that intentionally separate stable AES and
  drift-required tasks.

## Decision

Do not proceed to source repair v3 from this branch. There are no accepted
cells to use as repair ranges.

Route to branch synthesis:

```text
m1845-paper-route-executable-v2-reset-time-aes-feasibility-branch-synthesis
```

The synthesis should decide the next branch. The most likely pivot is a
task/source metadata redesign that first mines or constructs sources with
reset-time conditional support instead of trying to repair rows after
materialization.

## Guardrails

- additional project artifact scan: `false`
- source repair payload generated: `false`
- environment reset started: `false`
- environment rollout started: `false`
- policy action executed: `false`
- measured rollout started: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- reward changed: `false`
- dynamics changed: `false`
- termination behavior changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- M1843 no-support scan result is clean enough to close this source-repair
  route;
- branch synthesis is required before further repair or redesign;
- current M1825/M1828 stable AES-only target sources have no observed
  reset-time AES-only support in the scanned grid.

Unsupported:

- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
