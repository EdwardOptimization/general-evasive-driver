# M1742 Paper-Route Task-Quality Outcome Semantics Redesign

- status: completed
- decision: `outcome_semantics_redesign_admit_no_rollout_materialization_preflight`
- parent audit: `docs/m1741-paper-route-task-quality-repaired-taxonomy-outcome-dominance-result-audit.md`
- no rollout: true

## Why This Redesign Exists

M1740/M1741 showed diffuse outcome dominance: `143` dominant slices across all
`6` scenario families and all `12` profiles. This means the current repaired
taxonomy is executable but not a clean paper-route benchmark. The problem is not
a single bad profile or a single bad row. It is an evaluation semantics problem:
different scenario families are being forced through one success/off-track/
collision interpretation.

M1742 therefore redesigns the task-quality contract before any new rollout,
profile comparison, or paper-level claim.

## Global Semantics

Each future row must carry two explicit labels:

```text
evaluation_role:
  benchmark
  diagnostic_stress
  mitigation_diagnostic

primary_metric_family:
  avoidance_success
  controlled_drift_recovery
  collision_mitigation
  boundary_robustness
  hidden_dynamics_robustness
```

Top-level ranking, when eventually allowed, may only use `benchmark` rows.
`diagnostic_stress` and `mitigation_diagnostic` rows remain diagnostic panels
unless a later manifest explicitly promotes them with a pre-registered metric.

## Family Semantics

| family | evaluation role | primary metric | success/quality semantics |
| --- | --- | --- | --- |
| `ordinary_stable_avoidance` | `benchmark` | `avoidance_success` | Obstacle passed, no collision, no off-track termination, bounded sideslip/yaw, and recovery to stable corridor by episode end. |
| `aeb_infeasible_stable_aes` | `benchmark` | `avoidance_success` | Obstacle passed by steering/braking, no collision, no off-track termination, and bounded recovery time. |
| `drift_required_avoidance` | `benchmark` | `controlled_drift_recovery` | Obstacle passed, no collision, controlled high-yaw/sideslip allowed, but recovery and road-boundary constraints are mandatory. |
| `unavoidable_mitigation` | `mitigation_diagnostic` | `collision_mitigation` | Do not score as ordinary success. Measure impact severity, impact speed proxy, clearance margin, heading/yaw at contact, and whether the policy chose a lower-severity trajectory. |
| `off_track_boundary_stress` | `diagnostic_stress` | `boundary_robustness` | Do not mix into top-level success ranking. Measure off-track frequency, boundary margin, time-to-off-track, and recovery if boundary is crossed. |
| `hidden_dynamics_stress` | split by label | `hidden_dynamics_robustness` | For supported avoidance labels, use the corresponding benchmark metric; for stress/OOD labels, report robustness diagnostics separately. |

## Required Metrics

Future materialization should define these metric columns even if some are
initially approximated from existing rollout info:

```text
benchmark_success
avoidance_success
controlled_drift_recovery_success
collision_mitigation_score
impact_severity_proxy
off_track_violation
off_track_severity_proxy
recovery_success
recovery_time_proxy
diagnostic_only_no_ranking_claim
```

Unsupported or not-yet-measurable metrics must be recorded explicitly. They
must not be silently approximated into a paper claim.

## Aggregation Rules

Primary paper-route aggregates:

- `benchmark_success_rate` over `evaluation_role=benchmark` rows only;
- `collision_failure_rate` over benchmark rows;
- `off_track_violation_rate` over benchmark rows;
- `controlled_drift_recovery_success_rate` over drift-required benchmark rows;
- `hidden_dynamics_robustness_summary` as diagnostic until promoted.

Separate diagnostic aggregates:

- `mitigation_diagnostic_summary` for unavoidable rows;
- `boundary_stress_summary` for off-track stress rows;
- `diagnostic_stress_summary` for hidden-dynamics/OOD stress rows;
- profile-control aggregates kept diagnostic until a promotion manifest admits
  ranking.

## Claim Boundary

Allowed after this design:

- no-rollout materialization/preflight of revised semantics;
- explicit separation of benchmark and diagnostic rows;
- explicit unsupported metric reporting.

Still forbidden:

- environment rollout;
- controller-family ranking;
- profile promotion;
- paper-level benchmark evidence;
- level3 self-identification claims;
- treating unsupported fault-like features as covered.

## Decision

Admit M1743 no-rollout materialization/preflight.

M1743 should create durable semantics artifacts from this design, join them to
the existing scenario taxonomy families, verify that benchmark/diagnostic roles
are present, and check for unsupported metric gaps before any new rollout.
