# M2026 Paper-Route Controlled Comparison Source Coverage Repair Implementation

- status: completed
- decision: `controlled_comparison_source_coverage_repair_partial_route_to_result_audit`
- manifest: `experiments/manifests/m2026-paper-route-controlled-comparison-source-coverage-repair-implementation.json`
- implementation: `src/autodrift/paper_route_controlled_comparison_source_coverage_repair.py`
- focused tests: `1 passed`
- compileall: `passed`
- summary: `runs/m2026_paper_route_controlled_comparison_source_coverage_repair/summary.json`
- reset/rollout/measured execution in M2026: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Result

M2026 implemented and ran the no-rollout source coverage repair over existing
public artifacts only.

```text
result_class: controlled_comparison_source_coverage_repair_partial
base_source_count: 171
repaired_source_count: 183
added_source_count: 12
t1_candidate_count: 314
guardrail_violation_count: 0
panel_ready_for_routing_smoke: false
```

No environment reset, rollout, policy action, measured execution, replay, PPO,
training, private holdout, profile tuning, actor-input change, ranking claim,
paper-level claim, or level3 self-ID claim occurred.

## Coverage

Before/after coverage:

```text
T1_reactive_active_safety:
  before: count 6, source kinds 1, max share 1.0000
  after:  count 18, source kinds 4, max share 0.3333
  status: passes_after_repair

T2_same_current_different_older_history:
  before: count 36, source kinds 4, max share 0.5833
  after:  count 36, source kinds 4, max share 0.5833
  status: unchanged_unready

T3_active_diagnostic_warmup:
  before: count 24, source kinds 4, max share 0.3750
  after:  count 24, source kinds 4, max share 0.3750
  status: unchanged_unready

T4_variable_diagnostic_delay:
  status: already_ready

T5_source_rich_extreme_dynamics:
  status: already_ready
```

Ready families after repair:

```text
T1_reactive_active_safety
T4_variable_diagnostic_delay
T5_source_rich_extreme_dynamics
```

Unresolved families:

```text
T2_same_current_different_older_history
T3_active_diagnostic_warmup
```

## Repair Actions

M2026 added 12 clean T1 rows from M1983 outcome-support sources. The added
source kinds are source-diverse relative to the original T1 singleton:

```text
anchor_neighborhood
mitigation_isolation_check
offtrack_boundary_relief
```

The tool did not weaken thresholds, duplicate sources, relabel T4/T5 rows, or
pretend T2/T3 were fixed. It explicitly emitted unresolved actions:

```text
T2_same_current_different_older_history:
  unresolved_no_clean_topup_in_current_artifacts

T3_active_diagnostic_warmup:
  unresolved_no_clean_topup_in_current_artifacts
```

## Supported Claims

Supported:

```text
M2026 produced clean no-rollout source repair artifacts.
The T1 active-safety source count and source-kind singleton blocker is fixed.
T4/T5 passing source coverage is preserved.
The controlled-comparison panel is closer to execution readiness but still not
routing-smoke-ready.
```

Unsupported:

```text
The full panel is ready for routing smoke.
T2/T3 source-kind dominance is fixed.
Controller families can be ranked.
Finite-window-vs-GRU can be concluded.
Paper-level benchmark evidence exists.
Level3 self-identification evidence exists.
```

## Route Decision

Decision:

```text
route_to_source_coverage_repair_result_audit
```

Rationale:

- The repair successfully changed the evidence state by fixing T1.
- The panel still fails the registered source-kind share gate for T2/T3.
- The correct next step is an audit that decides whether T2/T3 require new
  same-family source generation, threshold/source-kind rule audit, split-panel
  routing, or branch synthesis.
- Direct routing smoke remains blocked because
  `panel_ready_for_routing_smoke=false`.

Failure taxonomy:

```text
scenario_sampling_failure:
  T2/T3 source-kind diversity cannot be repaired from the current public
  top-up artifacts without weakening thresholds or relabeling sources.
```

## Artifacts

```text
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/summary.json
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repaired_panel_sources.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repaired_source_coverage.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/coverage_comparison.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repair_actions.csv
runs/m2026_paper_route_controlled_comparison_source_coverage_repair/claim_boundary.csv
```

## M2027 Requirements

M2027 should audit M2026 without rerun or execution. Because the local-search
cadence fired, it must also be a branch synthesis milestone and decide whether
the next route is:

```text
new T2/T3 same-family source generation
threshold/source-kind semantics audit
split-panel routing smoke for ready families
stop current route
```

M2027 must not run environment rollout, train, replay, rank controller
families, or claim finite-window-vs-GRU/self-ID evidence.
