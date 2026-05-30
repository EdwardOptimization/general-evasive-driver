# M1744 Paper-Route Task-Quality Outcome Semantics Materialization Preflight Result Audit

- status: completed
- decision: `materialization_audit_route_to_metric_instrumentation_design`
- audited artifact: `runs/m1743_task_quality_outcome_semantics_materialization_preflight/summary.json`
- audited doc: `docs/m1743-paper-route-task-quality-outcome-semantics-materialization-preflight.md`
- no rollout: true

## Summary

M1744 audits the M1743 no-rollout materialization. The materialization is clean:
the revised semantics cover all repaired taxonomy rows, split benchmark,
diagnostic-stress, and mitigation-diagnostic roles, and record unsupported
metric gaps explicitly.

The audit does not admit direct execution. Several metric gaps are
benchmark-critical, so a revised rollout would either silently approximate
recovery/controlled-drift/mitigation metrics or compare profiles on a narrower
metric than the pre-registered semantics require.

## Audited Counts

| field | observed | audit decision |
| --- | ---: | --- |
| scenario specs | `72` | pass |
| scenario matrix cells | `864` | pass |
| scenario families | `6` | pass |
| profiles | `12` | pass |
| registry rows | `6` | pass |
| metric support rows | `11` | pass |
| registry metric errors | `0` | pass |
| unsupported metric gaps | `7` | explicit, blocks direct execution |
| silent unsupported approximations | `0` | pass |
| guardrail violations | `0` | pass |

Evaluation-role distribution:

```text
benchmark: 36 specs, 432 matrix cells
diagnostic_stress: 24 specs, 288 matrix cells
mitigation_diagnostic: 12 specs, 144 matrix cells
```

## Metric Gap Audit

M1743 records seven explicit gaps:

| metric | support status | audit impact |
| --- | --- | --- |
| `controlled_drift_recovery_success` | partial, needs recovery definition | blocks drift-required benchmark scoring |
| `collision_mitigation_score` | partial, needs metric definition | blocks unavoidable-mitigation diagnostic scoring |
| `impact_severity_proxy` | unsupported until instrumented | blocks mitigation severity evidence |
| `off_track_severity_proxy` | unsupported until instrumented | blocks boundary-stress severity evidence |
| `recovery_success` | partial, needs metric definition | blocks stable avoidance and drift recovery semantics |
| `recovery_time_proxy` | unsupported until instrumented | blocks benchmark recovery-time semantics |
| `hidden_dynamics_robustness` | partial, needs metric definition | blocks hidden-dynamics stress aggregate interpretation |

These are not cosmetic gaps. `recovery_success`, `recovery_time_proxy`, and
`controlled_drift_recovery_success` affect benchmark rows directly. Direct
execution would therefore create a result that is mechanically runnable but not
aligned with the revised semantics.

## Route Decision

Rejected routes:

- direct revised-semantics execution: blocked by benchmark-critical metric gaps;
- controller-family ranking: blocked, because benchmark semantics are not fully
  measurable yet;
- bounded supported-only panel as main route: possible as a later diagnostic,
  but it would dodge the drift-required, mitigation, boundary, and
  hidden-dynamics semantics that the paper route needs.

Admitted route:

- M1745 outcome metric instrumentation design.

M1745 should define logging and aggregate semantics for recovery, recovery
time, controlled drift recovery, impact severity, off-track severity, and
hidden-dynamics robustness before any implementation or rerun.

## Claim Boundary

Supported:

- M1743 materialization is complete and guardrail-clean;
- the explicit metric gaps are known and non-silent;
- direct execution is blocked until metric definitions/instrumentation are
  designed.

Unsupported:

- rollout result under revised semantics;
- profile ranking or promotion;
- paper-level benchmark evidence;
- recurrent advantage;
- level3 self-identification.

## Decision

Route to M1745 paper-route task-quality outcome metric instrumentation design.
