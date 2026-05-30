# M1845 Paper Route Executable V2 Reset-Time AES Feasibility Branch Synthesis

- status: completed
- synthesis decision: `pivot`
- completed branch: `paper_route_executable_v2_reset_time_aes_feasibility_scan`
- next branch: `paper_route_executable_v2_task_source_metadata_redesign`
- additional scan run: `false`
- environment reset run: `false`
- rollout/training/replay/PPO: `false`

## Evidence Summary

M1830-M1844 investigated why the executable-v2 stable AES rows could not pass
reset-time sampling after source materialization and source-range repair.

Key evidence:

- M1830-M1832 designed and pre-registered reset-time AES sampler diagnostics.
- M1833 replayed reset-time sampler attempts for the `24` failed AES rows:
  `240000` attempts, `0` accepted, all selected attempts rejected as
  `aeb_feasible`.
- M1834 classified the first diagnostic as a need for reset-time AES-only source
  repair, while also recording a row/attempt aggregation artifact in the
  earlier diagnostic summary.
- M1835-M1838 designed, implemented, and ran source repair v2. It tried `10`
  candidate rows over `1200000` attempts and still found `0` accepted profiles.
- M1839 audited M1838 as static candidate-space failure, not task impossibility,
  and required a conditional speed/mu feasibility scan before further repair.
- M1840-M1843 designed, implemented, pre-registered, and ran that conditional
  scan.
- M1843 scanned:

  ```text
  24 profiles * 120 distances * 61 half-widths = 175680 cells
  ```

  Result:

  ```text
  result_class: reset_time_aes_feasibility_scan_no_support
  accepted_cell_count_total: 0
  feasible_profile_count_total: 0
  feasible_source_count: 0
  guardrail_violation_count: 0
  ```

- M1844 audited the result as clean no-support for the current stable AES-only
  source-repair route, with one minor claim-boundary wording artifact in the
  helper-produced claim CSV.

The decisive M1843 label distribution:

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

There were no `aes_feasible` cells to repair toward.

## Supported Claims

Supported:

- The current M1825/M1828 stable AES-only target sources do not have observed
  reset-time AES-only support in the scanned conditional grid.
- Blind source-range widening is the wrong control variable for this branch.
- Source repair v3 from accepted cells is impossible for this branch because
  there are no accepted cells.
- The executable-v2 metadata guardrails remain clean: no actor-input label
  leakage, no ranking admission, no reset/rollout/policy action in diagnostics.
- The next branch should be support-first: find or construct reset-time
  conditional support before materializing executable-v2 profile rows.

Unsupported:

- Full executable-v2 reset feasibility.
- Stable AES source repair success.
- Measured execution readiness.
- Controller-family ranking.
- Private-holdout evidence.
- Paper-level benchmark evidence.
- Level3 self-identification.

## Falsified Claims

Falsified for this source-repair route:

- Offline source density or static candidate ranges are sufficient to predict
  reset-time stable AES support.
- The two current stable AES source families can be rescued by further blind
  range widening.
- The current failed AES rows contain a stable AES-only obstacle cell somewhere
  in `[1.0, 60.0] x [0.2, 1.4]` under their reset-time speed/mu conditions.
- A source repair v3 payload can be generated from M1843 accepted cells.

Not falsified:

- Executable-v2 panels as a general paper route.
- Drift-required or unavoidable task rows.
- A future stable AES panel mined from sources with real reset-time conditional
  support.
- The broader RL driver research goal.

## Failure Taxonomy Summary

Primary failure:

```text
scenario_sampling_failure -> source_task_support_absence_for_stable_aes_only
```

Evidence:

- M1833: `240000` reset-time attempts, `0` accepted.
- M1838: `1200000` candidate attempts, `0` accepted profiles.
- M1843: `175680` deterministic grid cells, `0` accepted `aes_feasible` cells.

Secondary process artifact:

```text
metric_artifact -> claim_boundary_context_wording_artifact
```

The M1843 helper-written claim boundary retained M1841 implementation-only
wording. It did not affect scan counts, but future helper outputs should use
context-aware claim-boundary rows.

No actor-input contract violation, reward change, dynamics change, termination
change, profile-specific tuning, ranking claim, paper-level claim, or level3
self-ID claim occurred.

## Public Gate Overfit Risk

The branch overfit risk is now clear: we were trying to rescue a fixed set of
materialized rows after they had already become unsupported stable-AES tasks.
That creates a local loop:

```text
materialize rows -> reset fails -> widen ranges -> reset still fails
```

The correct workflow is the opposite:

```text
support scan / source mining -> materialize only supported role rows -> reset validation
```

The next branch should make task-source metadata support-first. It should not
start by generating another repaired payload over the same two unsupported AES
sources.

## Next Branch Decision

Decision:

```text
pivot
```

Completed branch:

```text
paper_route_executable_v2_reset_time_aes_feasibility_scan
```

Next branch:

```text
paper_route_executable_v2_task_source_metadata_redesign
```

Next milestone:

```text
m1846-executable-v2-task-source-metadata-redesign-design
```

M1846 should design a support-first source/task metadata contract:

- source candidates must prove reset-time conditional support before
  executable-v2 materialization;
- stable AES and drift-required roles must be separated instead of forcing
  `aes_feasible` labels onto drift-required/unavoidable cells;
- claim-boundary output must be context-aware for helper implementation,
  project-artifact execution, and result audit;
- no actor inputs, reward, dynamics, or termination behavior should change.

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

- reset-time AES feasibility branch synthesis;
- pivot away from current stable AES-only source repair route;
- need for support-first task/source metadata redesign.

Unsupported:

- source repair success;
- repaired reset feasibility;
- measured execution;
- controller-family ranking;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.
