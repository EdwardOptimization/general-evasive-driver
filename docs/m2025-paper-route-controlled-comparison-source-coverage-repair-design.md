# M2025 Paper-Route Controlled Comparison Source Coverage Repair Design

- status: completed
- decision: `controlled_comparison_source_coverage_repair_design_admit_no_rollout_implementation`
- blocker source: `docs/m2024-paper-route-controlled-comparison-panel-preflight-result-audit.md`
- current preflight: `runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json`
- source coverage: `runs/m2023_paper_route_controlled_comparison_panel_preflight/source_coverage.csv`
- reset/rollout/measured execution in M2025: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Purpose

M2025 designs a bounded no-rollout source-coverage repair for the controlled
comparison panel. The repair must fix the M2023 readiness blocker without
weakening the M2022 evidence standard.

Allowed:

```text
select additional clean sources
rebalance source-kind dominance
deduplicate source-heavy cells
preserve all 12 controller profiles
preserve T4/T5 passing coverage unless explicitly justified
```

Not allowed:

```text
change actor inputs
change controller profiles
change action space
lower thresholds just to pass
run environment rollout
rank controllers
claim finite-window-vs-GRU or self-ID evidence
```

## Starting Gaps

From M2023/M2024:

```text
T1_reactive_active_safety:
  source_count = 6
  source_kind_count = 1
  max_single_source_kind_share = 1.0000
  target: count >= 12 and share <= 0.35

T2_same_current_different_older_history:
  source_count = 36
  source_kind_count = 4
  max_single_source_kind_share = 0.5833
  target: share <= 0.35

T3_active_diagnostic_warmup:
  source_count = 24
  source_kind_count = 4
  max_single_source_kind_share = 0.3750
  target: share <= 0.35

T4_variable_diagnostic_delay:
  passes current thresholds

T5_source_rich_extreme_dynamics:
  passes current thresholds
```

## Candidate Source Artifacts

Use only existing public artifacts in the first repair implementation.

T1 active-safety top-up candidates:

```text
runs/m1983_executable_v2_task_quality_calibrated_outcome_support_source_mining/outcome_support_source_rows.csv
runs/m1952_executable_v2_task_quality_offtrack_support_repair_calibrated_source_mining/repair_source_rows.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/source_kind_aggregate.csv
runs/m2009_executable_v2_task_quality_calibrated_repaired_outcome_support_measured_execution_rerun_selection_quota_compat/role_surface_aggregate.csv
runs/m2018_source_diverse_diagnostic_expansion_mining/admitted_expansion_candidates.csv
```

M1983 and M1952 provide supported source rows with repair-source kinds beyond
the M2020 `success_stabilizer` singleton. M2009 aggregate tables are audit
context only; they should not be treated as executable source rows by
themselves.

T2/T3 rebalance candidates:

```text
runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json
runs/m1683_controller_family_bounded_rollout_protocol_preflight/workload_matrix.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/panel_sources.csv
```

These artifacts already contain T2/T3 source rows. The repair should first try
quota rebalancing and non-dominant top-up from the same public source pool
before designing new scenario generation.

## Repair Rules

### T1 Active-Safety Repair

Repair objective:

```text
count >= 12
max_single_source_kind_share <= 0.35
roles preserved:
  stable_aeb
  stable_aes_only
  drift_required_recovery
  unavoidable_mitigation
```

Selection rules:

```text
1. Keep the six M2020 active-safety diagnostic sources as seed rows.
2. Add supported rows from M1983/M1952 whose guardrails are clean:
   labels_enter_actor_input == False
   profile_specific_tuning == False
   controller_family_ranking_claim_made == False
   paper_level_claim_made == False
   level3_self_id_claim_made == False
3. Prefer repair_source_kind values not already present in T1.
4. Keep role/surface/label coverage balanced where possible.
5. If no feasible mix can reduce max source-kind share <= 0.35, fail closed
   and route to threshold/source-generation audit rather than lowering the
   threshold.
```

### T2 Same-Current / Different-Older-History Repair

Current blocker:

```text
dominant kind: actuator_delay_proxy+capability_step_proxy
dominant count/share: 21 / 36 = 0.5833
```

Repair objective:

```text
count >= 24
max_single_source_kind_share <= 0.35
preserve same-current/different-older-history semantics
```

Selection rules:

```text
1. Preserve all non-dominant source kinds unless they duplicate exact source ids.
2. Cap the dominant source kind or add non-dominant source rows until share <=
   0.35.
3. Prefer explicit source families that still satisfy T4 semantics from the
   original M1680 lineage.
4. Do not reclassify T4/T5 rows as T2 merely to satisfy counts.
```

### T3 Active Diagnostic Warmup Repair

Current blocker:

```text
dominant share: 9 / 24 = 0.3750
```

Repair objective:

```text
count >= 24
max_single_source_kind_share <= 0.35
preserve warmup semantics
```

Selection rules:

```text
1. Prefer adding non-dominant warmup sources before dropping existing rows.
2. If only one or two top-up rows are needed, keep the repair minimal.
3. Do not invent active-probing actions outside the existing P0 actor contract.
```

### T4/T5 Preservation

T4 and T5 already pass the registered thresholds:

```text
T4 source count 33, max share 0.2727
T5 source count 72, max share 0.2917
```

The repair must preserve those rows unless deduplication is necessary to keep a
single source id from appearing in incompatible families. If T4/T5 are changed,
the implementation must report before/after coverage.

## M2026 Output Contract

M2026 should implement a no-rollout repair preflight. It should write:

```text
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/summary.json
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repaired_panel_sources.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repaired_source_coverage.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repair_actions.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/claim_boundary.csv
```

Expected decision classes:

```text
controlled_comparison_source_coverage_repair_pass:
  T1/T2/T3 gaps are repaired and T4/T5 remain passing.

controlled_comparison_source_coverage_repair_partial:
  at least one gap improves but the panel is still not routing-smoke-ready.

controlled_comparison_source_coverage_repair_fail_closed:
  no clean repair is possible from current public artifacts.
```

Any partial or fail-closed result must route to audit, not execution.

## Claim Boundary

M2025 is a design milestone only. It supports:

```text
source-coverage repair route is defined
candidate artifacts are named
repair constraints are explicit
```

It does not support:

```text
routing-smoke readiness
controller-family ranking
finite-window-vs-GRU conclusion
paper-level benchmark evidence
level3 self-identification
```
