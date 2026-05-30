# M1834 Executable V2 Reset-Time AES Sampler Diagnostic Result Audit

- status: completed
- decision: `reset_time_aes_sampler_audit_route_to_source_repair_v2_design`
- branch: `paper_route_executable_v2_reset_time_aes_sampler_diagnostic`
- parent artifact: `runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/summary.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1834 audits the M1833 reset-time AES sampler diagnostic result. It decides
whether the persistent M1828 AES failures are explained well enough to design a
source repair v2. This milestone does not run reset, rollout, measured
execution, training, replay, PPO, ranking, or any actor-input change.

## Audited Artifacts

```text
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/summary.json
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/aes_source_diagnostic_targets.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/offline_density_rows.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_attempt_summary.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_reject_reason_counts.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_label_counts.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/reset_time_candidate_examples.csv
runs/m1833_executable_v2_reset_time_aes_sampler_diagnostic/claim_boundary.csv
```

## Count Audit

The detailed CSVs are internally consistent:

| field | value |
| --- | ---: |
| diagnostic target rows | 24 |
| sources | 2 |
| profiles per source | 12 |
| attempts per profile row | 10000 |
| total attempts | 240000 |
| accepted candidates | 0 |
| guardrail violations | 0 |

Per-source totals:

| source | failed profile rows | attempts | accepted | offline density | reset-time density |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m1771-bp1-00` | 12 | 120000 | 0 | 0.0035555555555555557 | 0.0 |
| `m1771-bp1-02` | 12 | 120000 | 0 | 0.043555555555555556 | 0.0 |

Aggregate detailed labels:

| label | count |
| --- | ---: |
| `aeb_feasible` | 240000 |

Aggregate detailed reject reasons:

| reject reason | count |
| --- | ---: |
| `aeb_feasible_rejected` | 240000 |

The candidate examples agree with the full count tables: every shown candidate
is `aeb_feasible` and rejected by `require_aeb_infeasible`.

## Metric Artifact

`summary.json` reports:

```json
{
  "label_counts": {"aeb_feasible": 24},
  "reject_reason_counts": {"aeb_feasible_rejected": 24}
}
```

Those are row-level aggregates over the per-row count records, not total sampler
attempt counts. The detailed CSVs are the authoritative evidence for this audit.
The next implementation should repair or supplement summary aggregation so
future gates can read both:

```text
row_count_by_label
attempt_count_by_label
row_count_by_reject_reason
attempt_count_by_reject_reason
```

This is a `metric_artifact`, but it does not invalidate M1833 because the
detailed attempt-count CSVs are complete and consistent.

## Failure Classification

The current AES repair failed because the repaired source ranges do not produce
reset-time AES-only candidates under the executable reset sampler. They produce
AEB-feasible candidates instead, and the task explicitly requires
`require_aeb_infeasible=True` for these AES rows.

This is not evidence for:

- attempt-budget exhaustion;
- environment reset instability;
- rollout or policy behavior;
- controller ranking;
- level3 self-identification.

It is evidence for:

- `scenario_sampling_failure`: reset-time sampler support is incompatible with
  the repaired AES source ranges;
- `metric_artifact`: top-level summary counts are row counts, not attempt counts.

## Route Decision

Do not rerun reset yet. The next step should design source repair v2 around
reset-time sampler acceptance rather than offline density.

M1835 should require:

1. Target exactly the two persistent AES sources:
   `m1771-bp1-00` and `m1771-bp1-02`.
2. Search for ranges that produce `aes_feasible` candidates accepted under
   `require_aeb_infeasible=True` at reset time.
3. Treat offline density as diagnostic only, not as the acceptance objective.
4. Preserve all profile controls and history/observation contracts.
5. Keep measured execution, ranking, paper-level claims, and reset rerun blocked
   until repaired sources pass a reset-only preflight.
6. Add or require explicit attempt-count aggregation so this metric artifact is
   not repeated.

## Guardrails

- environment reset started: `false`
- environment rollout started: `false`
- measured rollout started: `false`
- policy action executed: `false`
- training started: `false`
- replay started: `false`
- PPO used: `false`
- promoted: `false`
- private holdout used: `false`
- actor input contract changed: `false`
- profile-specific tuning: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`
- guardrail violation count: `0`

## Claim Boundary

Supported:

- all 24 M1833 target rows were audited;
- both persistent AES sources were audited;
- the detailed tables show 240000 AEB-feasible rejections and zero accepted
  candidates;
- reset-time source repair v2 is the correct next route.

Unsupported:

- repaired reset feasibility;
- reset-time repair success;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Follow-Up

Route to:

```text
m1835-executable-v2-reset-time-aes-source-repair-v2-design
```

M1835 should be a design milestone. It should not run reset or materialize new
source rows yet.
