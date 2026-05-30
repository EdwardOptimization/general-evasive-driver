# M1839 Executable V2 Reset-Time AES Source Repair V2 Result Audit

- status: completed
- decision: `reset_time_aes_source_repair_v2_audit_route_to_feasibility_scan_design`
- branch: `paper_route_executable_v2_reset_time_aes_source_repair_v2`
- parent artifact: `runs/m1838_executable_v2_reset_time_aes_source_repair_v2/summary.json`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Purpose

M1839 audits the M1838 clean fail before any further repair or reset preflight.
The audit decides whether M1838 falsifies the task support itself or only the
static source-level candidate families used by M1836.

## Audited Artifacts

```text
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/summary.json
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_targets.csv
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_candidate_scores.csv
runs/m1838_executable_v2_reset_time_aes_source_repair_v2/reset_time_aes_source_repair_claim_boundary.csv
```

## Evidence

M1838 completed structurally:

| field | value |
| --- | ---: |
| `result_class` | `reset_time_aes_source_repair_v2_fail` |
| target sources | 2 |
| target profiles | 24 |
| repaired specs | 36 |
| guardrail violations | 0 |

Candidate-score evidence:

| field | value |
| --- | ---: |
| candidate rows | 10 |
| candidate attempt total | 1200000 |
| selected attempt total | 240000 |
| accepted profile count set | `{0}` |
| selected source count | 2 |
| accepted source count | 0 |

All candidate families failed:

```text
original_reset_replay
aes_reset_close_band
aes_reset_close_medium_band
aes_reset_threshold_band
aes_reset_wide_search_band
```

All selected attempts were:

```text
label: aeb_feasible
reject_reason: aeb_feasible_rejected
```

The M1834 summary aggregation issue was repaired in M1838:

```text
summary_aggregation_version = row_and_attempt_counts_v1
attempt_count_by_label = {"aeb_feasible": 240000}
attempt_count_by_reject_reason = {"aeb_feasible_rejected": 240000}
row_count_by_label = {"aeb_feasible": 2}
row_count_by_reject_reason = {"aeb_feasible_rejected": 2}
```

## Interpretation

M1838 proves that the static candidate families used by M1836 are insufficient.
It does not yet prove that reset-time AES-only support is impossible.

The key missing evidence is conditional feasibility. The current repair tries a
small set of fixed source-level obstacle ranges, then samples inside them. If a
profile's reset-time speed/mu pair needs a tighter or differently placed window,
static candidate sampling can still miss every AES-only cell.

The next step should answer this sharper question:

```text
For each failed AES reset row's sampled speed_ref and mu,
does any obstacle distance / half-width grid cell classify as aes_feasible
and survive require_aeb_infeasible plus timing/threshold filters?
```

If yes, source repair v3 should derive ranges from those cells. If no, the
current source metadata or task definition cannot support executable AES reset
rows and the branch should synthesize and pivot.

## Route Decision

Route to a design milestone for a reset-time conditional feasibility scan.

The scan should:

1. reuse reset RNG state and `speed_ref` / `initial_mu` from each target row;
2. sweep a broad obstacle grid, including closer distances than M1836;
3. apply the same label, AEB-infeasible, threshold, and friction timing filters;
4. report whether each profile row has any accepted AES-only cell;
5. aggregate per source and per profile;
6. produce range suggestions only after feasibility is observed;
7. keep reset, rollout, measured execution, ranking, and paper-level claims
   blocked.

## Failure Classification

M1838 remains:

- `scenario_sampling_failure`: static candidate ranges do not cover reset-time
  AES-only support;
- `metric_artifact`: repaired in M1838 by row and attempt aggregation, but kept
  in lineage because this branch was opened by the M1834 aggregation issue.

No evidence supports:

- repaired reset feasibility;
- policy behavior conclusions;
- controller ranking;
- level3 self-identification.

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

- M1838 is a clean negative result for static source-level candidate families;
- M1838 does not justify a reset preflight;
- conditional feasibility scan is the correct next route.

Unsupported:

- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Follow-Up

Route to:

```text
m1840-executable-v2-reset-time-aes-feasibility-scan-design
```

M1840 should design the scan only. It should not run the scan.
