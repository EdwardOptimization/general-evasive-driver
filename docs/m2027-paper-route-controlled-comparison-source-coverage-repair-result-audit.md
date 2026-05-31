# M2027 Paper-Route Controlled Comparison Source Coverage Repair Result Audit

- status: completed
- decision: `controlled_comparison_source_coverage_repair_synthesis_pivot_to_t2_t3_source_generation_design`
- synthesis decision: `pivot`
- audited summary: `runs/m2026_paper_route_controlled_comparison_source_coverage_repair/summary.json`
- audited coverage: `runs/m2026_paper_route_controlled_comparison_source_coverage_repair/coverage_comparison.csv`
- audited repair actions: `runs/m2026_paper_route_controlled_comparison_source_coverage_repair/repair_actions.csv`
- reset/rollout/measured execution in M2027: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2026 produced clean no-rollout source-repair artifacts and changed the panel
state:

```text
result_class: controlled_comparison_source_coverage_repair_partial
base_source_count: 171
repaired_source_count: 183
added_source_count: 12
guardrail_violation_count: 0
panel_ready_for_routing_smoke: false
```

Coverage after M2026:

```text
T1_reactive_active_safety:
  status = passes_after_repair
  count/share = 18 / 0.3333

T2_same_current_different_older_history:
  status = unchanged_unready
  count/share = 36 / 0.5833

T3_active_diagnostic_warmup:
  status = unchanged_unready
  count/share = 24 / 0.3750

T4_variable_diagnostic_delay:
  status = already_ready
  count/share = 33 / 0.2727

T5_source_rich_extreme_dynamics:
  status = already_ready
  count/share = 72 / 0.2917
```

The M2026 tool correctly refused to relabel, duplicate, or threshold-weaken
T2/T3:

```text
T2: unresolved_no_clean_topup_in_current_artifacts
T3: unresolved_no_clean_topup_in_current_artifacts
```

## Supported Claims

Supported:

```text
M2026 cleanly repaired T1 source count and source-kind singleton dominance.
T4/T5 readiness was preserved.
The current panel is still not ready for full routing smoke.
The unresolved blocker is localized to T2/T3 source-kind diversity.
The source-repair branch has reached a synthesis point instead of another
local repair step.
```

## Falsified Claims

Falsified or unsupported:

```text
Existing public top-up artifacts are sufficient to fully repair T1/T2/T3.
The controlled panel is ready for full routing smoke.
Threshold weakening is justified by M2026 artifacts.
Ready-family-only execution would answer the fair L0/L1/L2/L3 paper question.
M2026/M2027 provide controller ranking, finite-window-vs-GRU, paper-level, or
level3 self-ID evidence.
```

## Failure Taxonomy Summary

Primary failure type:

```text
scenario_sampling_failure
```

Interpretation:

- T1 was a real source coverage gap and is now repaired.
- T2/T3 are not code failures and not controller failures.
- T2/T3 lack enough same-family non-dominant source rows under the registered
  source-kind diversity gate.
- This should be handled by generating new source-diverse T2/T3 source rows or
  by a narrow semantics audit of the source-kind gate, not by execution.

## Public Gate Overfit Risk

Risk:

```text
medium-to-high if the project keeps repairing the same M2023 panel rows;
low if the next branch creates new T2/T3 source-diverse panel evidence before
execution.
```

Why:

- The current panel and source-kind thresholds are public workflow gates.
- Continuing to top up from the same artifacts after M2026 would become
  local search: the tool already reported no clean same-family top-up for
  T2/T3.
- Running only T1/T4/T5 would make the paper route favor already-ready
  families and leave same-current/older-history and warmup evidence unresolved.

## Route Options

Rejected:

```text
direct_full_routing_smoke:
  rejected because panel_ready_for_routing_smoke=false.

threshold_weakening_now:
  rejected because M2026 did not show the 0.35 source-kind cap is semantically
  wrong; it showed current source availability is insufficient.

split_ready_family_routing:
  rejected for now because it would skip T2/T3, the families most relevant to
  finite-window-vs-GRU and history-dependence claims.

another_same_artifact_repair:
  rejected because M2026 already failed closed for T2/T3 same-family top-up.

stop_paper_route:
  rejected because T1/T4/T5 are ready and T2/T3 have concrete generation
  targets.
```

Selected:

```text
pivot_to_t2_t3_same_family_source_generation_design
```

## Next Branch Decision

M2028 should design a no-rollout source-generation branch for T2/T3.

Required direction:

```text
T2_same_current_different_older_history:
  preserve matched-current and different-older-history semantics;
  add enough non-dominant same-family source rows to reduce max source-kind
  share from 0.5833 to <= 0.35;
  avoid reusing T4/T5 rows by relabeling.

T3_active_diagnostic_warmup:
  preserve deployable warmup semantics;
  add non-dominant warmup source rows so max source-kind share is <= 0.35 with
  slack.
```

Quantitative planning targets:

```text
T2:
  current dominant count appears fixed at 21/36.
  if retained, total count must reach at least 60 for 21/60 <= 0.35.
  therefore M2028 should design at least 24 clean non-dominant same-family
  source rows, preferably with additional slack.

T3:
  current dominant count appears fixed at 9/24.
  at least 2 clean non-dominant rows would satisfy 9/26 <= 0.35.
  M2028 should target a larger source-diverse warmup set rather than a
  two-row edge pass.
```

M2028 must remain no-rollout design only. It should pre-register the exact
source-generation semantics, quotas, guardrails, artifacts, and audit route.
Execution, controller ranking, finite-window-vs-GRU conclusions, paper-level
claims, and level3 self-ID claims remain blocked.
