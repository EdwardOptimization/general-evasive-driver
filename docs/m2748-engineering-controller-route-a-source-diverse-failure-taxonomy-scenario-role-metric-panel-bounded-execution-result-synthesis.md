# M2748 Engineering Controller Route A Source-Diverse Failure Taxonomy Scenario-Role Metric Panel Bounded Execution Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_route_a_baseline_readiness_after_role_panel_diagnostic_index`
- manifest: `experiments/manifests/m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-synthesis.json`
- synthesis artifact: `docs/m2748-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-synthesis.md`
- parent audit: `docs/m2747-engineering-controller-route-a-source-diverse-failure-taxonomy-scenario-role-metric-panel-bounded-execution-result-audit.md`
- parent summary: `runs/m2746_engineering_controller_route_a_source_diverse_failure_taxonomy_scenario_role_metric_panel_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2749-engineering-controller-route-a-baseline-readiness-after-role-panel-diagnostic-index-materialization-preflight.json`
- next: `m2749-engineering-controller-route-a-baseline-readiness-after-role-panel-diagnostic-index-materialization-preflight`

## Evidence Summary

M2742-M2747 completed a full Route A role-panel branch after the M2740
failure taxonomy:

```text
M2742 design:
  scenario roles: 6
  admitted future target role: offtrack_containment_target
  guard/context roles: collision_caution_guard, diagnostic_success_context,
    negative_context_guardrail, blocked_same_surface_guard,
    protected_hf3_exclusion_guard

M2743 materialization:
  scenario role rows: 6
  metric contract rows: 6
  target panel rows: 18
  guardrail context rows: 5
  actor-contract guard rows: 16
  claim-boundary rows: 31
  gate rows: 22

M2746 bounded diagnostic execution:
  candidate rows: 14
  resolved candidates: 14
  execution rows: 14
  execution failure rows: 0
  guardrail context rows: 5
  actor-contract guard rows: 18
  claim-boundary rows: 34
  gate rows: 21
```

M2746 produced new closed-loop diagnostic data, but the result is weak and
does not justify direct interpretation:

```text
diagnostic success: 1
diagnostic collision: 1
off_track: 9
speed_too_low: 3
unset_or_completed: 1
```

M2747 audited and accepted M2746 as complete and claim-safe. It also rejected
using those rows as repair success, driver performance, validation readiness,
source-family ranking, task-family ranking, profile ranking, current-sim
verdict, paper evidence, high-fidelity evidence, full-driver completion, or
self-identification evidence.

The branch changed the evidence state by turning the M2740 taxonomy into an
actor-invisible scenario-role metric panel and then producing bounded
closed-loop diagnostic rows over the offtrack target role. It did not change
the driver-performance state enough to admit validation, promotion, or another
same-panel execution.

The guardrail surface remained intact:

```text
collision caution rows: 1, not executed
diagnostic success context rows: 3, not executed
negative-context guard rows: 31, not executed
blocked same-surface guard rows: 1, not executed
protected/HF3 exclusion rows: 11, not executed
guardrail rows in ordinary success denominator: false
actor observation shape: 72
action shape: 3
hidden/oracle actor input detected: false
actor-visible labels or verdicts: false
```

## Supported Claims

M2748 supports these limited claims:

```text
M2742-M2747 form a complete Route A source-diverse failure-taxonomy
scenario-role metric panel branch.

M2746 produced complete and claim-safe bounded role-panel closed-loop
diagnostic execution rows over 14 audited offtrack target rows.

The branch preserved the P0 actor contract: observation shape 72, action shape
3, no hidden/oracle actor input, and no actor-visible scenario-role, metric,
target, protected, blocker, route, success/progress, or verdict labels.

Collision caution, diagnostic success context, negative-context, blocked
same-surface, protected, and HF3 rows remained non-executed guardrails outside
ordinary success denominators.

The M2746 result is sufficient to update Route A readiness/admission state:
the known failure taxonomy and scenario-role metric report now have a bounded
role-panel execution diagnostic attached to them.
```

## Falsified Claims

M2748 rejects these interpretations:

```text
M2746 proves repair success.
M2746 proves driver performance.
M2746 proves validation readiness or a validation result.
M2746 ranks source families, task families, profiles, scenario roles, or
controller families.
M2746 selects a winner or promotes a checkpoint.
M2746 proves a current-sim verdict.
M2746 proves high-fidelity validation readiness or a high-fidelity result.
M2746 proves paper evidence, finite-window-vs-GRU evidence, full ideal driver
completion, or level3 self-identification.
```

M2748 also rejects another immediate M2746-like execution over the same role
panel. The branch already designed, materialized, audited, executed, and
audited that surface. Repeating it would increase row count while preserving
the same weak evidence question.

## Failure Taxonomy Summary

- `contract_violation`: not observed. Actor 72/action 3 and no hidden/oracle
  actor input remain intact.
- `lineage_invalid`: not observed. The branch traces from M2740 taxonomy
  through M2742 design, M2743 materialization, M2745 execution design, M2746
  execution, and M2747 audit.
- `metric_artifact`: controlled. Scenario-role, source-family, task-family,
  and profile context remains diagnostic and non-ranking.
- `scenario_sampling_failure`: active. The role-panel execution remains
  offtrack/speed dominated with only one diagnostic success row.
- `behavior_regression`: active as caution, not as a verdict. The collision
  row and speed-too-low rows must remain visible in future readiness indexing.
- `objective_overfit`: high if the branch continues with another same role
  panel execution or repair loop without a new evidence surface.
- `proof_washout`: controlled. M2748 explicitly rejects performance,
  validation, paper, current-sim, high-fidelity, full-driver, and self-ID
  claims from M2746.

## Public Gate Overfit Risk

Risk entering M2748: `medium-high`.

Reason:

```text
M2740-M2747 turned one source-diverse diagnostic surface into taxonomy,
scenario-role metric materialization, bounded execution, and audit. That was
useful, but the executed result is weak and another same-panel execution would
mostly optimize or count the same public current-sim surface.
```

Risk after M2748: `medium` only if the branch pivots to a refreshed Route A
readiness/admission index. Risk remains high if the next step is another
M2746-like execution, a same-surface repair route, or a performance packaging
claim.

Route constraints:

```text
Do not schedule another role-panel execution before a new readiness/admission
index identifies a changed evidence surface.

Do not rank M2693 versus M2716, T4 versus T5, profiles, or scenario roles from
M2746 rows.

Do not treat diagnostic success count as a success-rate verdict.

Do not execute collision caution, diagnostic success context, negative-context,
blocked same-surface, protected, or HF3 rows.

Keep current-sim as diagnostic rather than the final validation layer.
```

## Next Branch Decision

Decision:

```text
pivot_to_route_a_baseline_readiness_after_role_panel_diagnostic_index
```

The next bounded route is:

```text
m2749-engineering-controller-route-a-baseline-readiness-after-role-panel-diagnostic-index-materialization-preflight
```

M2749 should materialize a Route A readiness/admission index from existing
artifacts only. It should integrate:

```text
M2748 synthesis and M2747 audit
M2746 role-panel execution diagnostics
M2743 scenario-role metric panel
M2740 known failure taxonomy
M2667 readiness-after-protected-taxonomy index
M2541 baseline checkpoint list and actor I/O contract
M2505 public benchmark pack
M2508 runtime/inference-cost report
M2638 HF3 source dependency blocker
docs/post-m2470-route-plan.md
```

The index should answer which Route A deliverables are still current, which
blockers remain active, and what next non-overfit evidence route is admissible.
It may admit a future execution, packaging, Route B comparison, or Route C/HF
dependency route only after preserving claim boundaries. It must not itself
run reset, step, rollout, replay, validation, training, PPO, source build,
adapter probe, external simulation, ranking, winner selection, promotion,
success-rate verdict computation, or performance interpretation.

Rationale:

```text
Stopping the whole project is wrong because the full ideal driver gate has not
passed.

Continuing the same role-panel branch is local search because M2746 already
ran the bounded execution and M2747 accepted the result as complete but weak.

Direct validation, ranking, promotion, performance, paper, current-sim,
high-fidelity, full-driver, or self-ID interpretation is forbidden by M2747.

The highest leverage next action is to refresh Route A readiness/admission
after the role-panel diagnostic, so the project chooses the next evidence route
from the whole current artifact set instead of continuing a narrow panel loop.
```

## Claim Boundary

Allowed M2748 claim:

```text
M2742-M2747 are a complete claim-safe role-panel diagnostic branch, and their
weak M2746 result requires pivoting to a refreshed Route A readiness/admission
index before any further execution, repair, validation, ranking, or packaging
claim.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
profile ranking
task-family ranking
scenario-role ranking
winner selection
checkpoint promotion
success-rate verdict
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
level3 self-identification
```
