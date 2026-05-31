# M1948 Executable V2 Task-Quality Offtrack Support Repair Source-Mining Result Audit

- status: completed
- decision: `task_quality_offtrack_support_repair_source_mining_audit_route_to_anchor_fallback_geometry_calibration`
- branch: `paper_route_task_quality_offtrack_support_repair`
- audited source: `runs/m1947_executable_v2_task_quality_offtrack_support_repair_source_mining/summary.json`
- reset/rollout/measured execution in M1948: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M1947 implemented the no-rollout source-mining adapter and produced complete
artifacts, but it did not pass the pre-registered source-kind support gate.
M1948 audits the failure before any repair. This milestone does not rerun
source mining, does not change thresholds, and does not interpret controller
performance.

## M1947 Result Snapshot

Clean execution properties:

```text
input_template_count: 160
source_candidate_count: 160
resolution_failure_count: 0
accepted_cell_count_total: 1949
supported_source_count: 66
public_gate_supported_source_count: 40
guardrail_violation_count: 0
```

Source-kind support:

```text
anchor_neighborhood:        0 / 64 supported
success_stabilizer:        39 / 48 supported
offtrack_boundary_relief:  11 / 32 supported
mitigation_isolation_check: 16 / 16 supported
```

The broad source support gates passed:

```text
supported_source_count >= 64: true
public_gate_supported_source_count >= 24: true
```

The failure is therefore not a total source-mining failure. It is concentrated
in the `anchor_neighborhood` group.

## Failure Localization

All `64` anchor-neighborhood rows are slice-level stable-AEB anchors. They do
not have exact M1928 source ids, so M1947 used the fallback geometry defined in
M1946.

The blocked rows show the same failure pattern:

```text
source_role_semantics: stable_aeb
parent_sampled_obstacle_label: aeb_feasible
source_support_status: unsupported
source_support_failure_reason: label_role_mismatch
accepted_cell_count: 0
dominant_label: aes_feasible
dominant_reject_reason: label_not_allowed
```

This means the fallback geometry for stable-AEB anchor rows is too hard for the
stable-AEB source classifier. It maps to `aes_feasible`, while the anchor rows
require `aeb_feasible`.

This does not indicate:

- a code crash;
- missing M1945/M1928 artifacts;
- resolution failure;
- environment reset or rollout failure;
- actor input contract drift;
- profile-specific tuning;
- controller-family ranking evidence;
- paper-level evidence;
- level3 self-identification evidence.

## Route Decision

The right next route is:

```text
anchor fallback geometry calibration
```

M1949 should design a no-rollout calibration step that finds stable-AEB
fallback geometry whose classifier support matches `aeb_feasible`, then feeds
that calibrated fallback back into a source-mining rerun or adapter repair.

This is narrower than broader scenario redesign because the rest of M1947 is
healthy:

- total support is above floor;
- public-gate support is above floor;
- success-stabilizer support is above floor;
- offtrack-boundary-relief support is above floor;
- mitigation-isolation support is complete;
- guardrails are clean.

This is also not a threshold-relaxation route. The failed anchor rows should
not be accepted as stable-AEB anchors while their dominant label remains
`aes_feasible`.

## Supported Claims

M1948 supports:

- M1947's failure is localized to stable-AEB anchor fallback geometry;
- the offtrack-support repair branch is still salvageable without broad
  scenario redesign;
- M1949 should calibrate fallback geometry before another source-mining run;
- ranking, paper, and level3 self-ID claims remain blocked.

## Unsupported Claims

Still unsupported:

- offtrack support repair success;
- reset validity for the repaired source set;
- measured execution readiness;
- controller-family ranking;
- finite-window vs GRU conclusion;
- paper-level benchmark result;
- level3 self-identification.

## Next

Next milestone:

```text
m1949-executable-v2-task-quality-offtrack-support-repair-anchor-fallback-geometry-calibration-design
```

M1949 should design the exact no-rollout calibration command, outputs, and pass
gates. It should not run reset, rollout, measured execution, PPO, or controller
ranking.
