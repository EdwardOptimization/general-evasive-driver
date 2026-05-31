# M2023 Paper-Route Controlled Comparison Panel Preflight Implementation

- status: completed
- decision: `controlled_comparison_panel_preflight_source_repair_required_route_to_result_audit`
- result class: `controlled_comparison_panel_preflight_source_repair_required`
- implementation: `src/autodrift/paper_route_controlled_comparison_panel_preflight.py`
- focused tests: `1 passed`
- compileall: `passed`
- summary: `runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json`
- reset/rollout/measured execution in M2023: `false`
- policy action execution in M2023: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Command

```bash
PYTHONPATH=src python -m autodrift.paper_route_controlled_comparison_panel_preflight \
  --task-specs runs/m1680_controller_family_bounded_task_source_generation_preflight/task_source_specs.json \
  --candidate-support runs/m2020_multi_slice_bounded_diagnostic_comparison/candidate_support.csv \
  --m1683-summary runs/m1683_controller_family_bounded_rollout_protocol_preflight/summary.json \
  --output-dir runs/m2023_paper_route_controlled_comparison_panel_preflight \
  --next-blocker m2024-paper-route-controlled-comparison-panel-preflight-result-audit
```

## Result

```text
result_class: controlled_comparison_panel_preflight_source_repair_required
profile_count: 12
task_family_count: 5
panel_source_count: 171
workload_cell_count: 2052
panel_ready_for_routing_smoke: false
guardrail_violation_count: 0
```

Coverage checks:

```text
profile_count: true
all_task_families_present: true
min_family_source_count: false
target_family_source_count: false
source_kind_share: false
m1683_guardrail: true
```

Source coverage:

```text
T1_reactive_active_safety:
  sources 6, source kinds 1, max source-kind share 1.0000
  min count pass false, target pass false, source-kind share pass false

T2_same_current_different_older_history:
  sources 36, source kinds 4, max source-kind share 0.5833
  min count pass true, target pass true, source-kind share pass false

T3_active_diagnostic_warmup:
  sources 24, source kinds 4, max source-kind share 0.3750
  min count pass true, target pass true, source-kind share pass false

T4_variable_diagnostic_delay:
  sources 33, source kinds 4, max source-kind share 0.2727
  min count pass true, target pass true, source-kind share pass true

T5_source_rich_extreme_dynamics:
  sources 72, source kinds 8, max source-kind share 0.2917
  min count pass true, target pass true, source-kind share pass true
```

## Interpretation

Supported:

```text
M2023 can materialize the M2022 controlled-comparison design into no-rollout
protocol artifacts with all five task families present, all 12 profiles, 171
panel sources, 2052 workload cells, and zero guardrail violations.
```

Also supported:

```text
The controlled panel is not ready for routing smoke. T1 is below the minimum
source count and source-kind diversity target, and T2/T3 exceed the max
single-source-kind share target.
```

Unsupported:

```text
controller-family ranking
finite-window-vs-GRU conclusion
paper-level benchmark evidence
level3 self-identification
routing-smoke readiness
```

This is useful negative process evidence: the next step should audit whether to
repair T1/T2/T3 source coverage or revise the panel thresholds. It should not
execute the current workload as if it were comparison-ready.

## Artifacts

```text
runs/m2023_paper_route_controlled_comparison_panel_preflight/summary.json
runs/m2023_paper_route_controlled_comparison_panel_preflight/panel_protocol.json
runs/m2023_paper_route_controlled_comparison_panel_preflight/workload_matrix.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/source_coverage.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/panel_sources.csv
runs/m2023_paper_route_controlled_comparison_panel_preflight/claim_boundary.csv
```

## Validation

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_paper_route_controlled_comparison_panel_preflight.py
python -m compileall -q src tests
```

Both passed before final validation.

## Next

M2024 should audit the preflight result. The audit must decide whether:

```text
1. T1/T2/T3 source repair should be designed before routing smoke;
2. the source-kind share thresholds should be revised with justification;
3. the panel should be split into a ready T4/T5 routing smoke and a repaired
   T1/T2/T3 branch;
4. or the branch should synthesize before another repair milestone.
```

No environment rollout or ranking is admitted until M2024 chooses a route.
