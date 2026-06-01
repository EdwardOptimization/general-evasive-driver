# M2135 Paper-Route Outcome-Supported Decisive Comparison-Support Branch Synthesis

- status: completed
- decision: `comparison_support_branch_synthesis_continue_to_controlled_panel_audit`
- synthesis_decision: `continue`
- synthesis window: `M2125-M2134`
- reset/rollout/measured execution in M2135: `false`
- policy actions executed in M2135: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

The branch changed from a raw complete measured artifact into a bounded,
non-overlapping controlled-panel artifact:

```text
M2125 measured execution: 1200/1200 episodes, failure 0, validation 0,
metadata 0, metric completeness 0, guardrail 0.

M2128 localization: outcome counts reproduced exactly; 15 comparison-ready
candidates, 37 candidate-support slices, 92 offtrack-dominance slices, 27
collision-dominance slices.

M2131 qualification: source ready/support counts 15/37 reproduced; 15
qualified candidates, 37 diagnostic-only support rows, axis coverage true,
guardrail 0.

M2134 controlled panel construction: 6 primary source-kind panel units, 9
excluded qualified rows, duplicate source-kind count 0, broad aggregate
exclusions 3, guardrail 0.
```

The branch therefore created a usable pre-comparison panel artifact. It did not
run a comparison and did not rank profiles.

## Supported Claims

Supported:

```text
The comparison-support scenario branch can produce a complete measured artifact
and a non-overlapping six-unit controlled panel from generated smoke-proxy
tasks without rerun after M2125.
```

Also supported:

```text
The earlier low-support blocker from the public-gate core panel is no longer a
zero-support blocker: this branch has 188 raw successes, 15 qualified
comparison-ready rows, and 6 controlled panel units.
```

## Falsified Claims

Falsified or still unsupported:

```text
No paper-level benchmark result is supported because all rows are generated
comparison-support smoke proxies with paper_validity_claim=false.

No controller-family ranking is supported because no controlled comparison
protocol has been designed or executed.

No finite-window-vs-GRU conclusion is supported because the panel has not been
converted into a controlled comparison.

No level3 self-identification claim is supported because no history-necessity
intervention is tested in this branch segment.
```

## Failure Taxonomy Summary

No new failure taxonomy label is active in M2125-M2134.

The main risk is not an execution failure; it is evidence interpretation:

```text
metric_artifact risk: profile aggregates could be mistaken for ranking.
objective_overfit/public-gate risk: generated support proxy rows are not
paper-valid tasks.
lineage risk: broad aggregate rows and source-kind rows could double-count the
same support if used directly.
```

M2134 reduces the double-counting risk by constructing one canonical panel unit
per source kind.

## Public Gate Overfit Risk

Risk remains medium.

Reasons:

```text
the panel is generated from comparison-support proxy tasks;
paper_validity_claim remains false;
private holdout is not used;
the controlled panel has only 6 primary units;
outcomes remain localized but not yet compared under a protocol.
```

The branch should continue only to audit the controlled panel and design a
comparison protocol. It should not jump directly to ranking.

## Next Branch Decision

Decision: `continue`.

Reason:

```text
The branch produced new measured evidence and a new non-overlapping panel, so
it is not merely local process churn. The next high-leverage step is to audit
the controlled panel and then design a comparison protocol if the audit passes.
```

Immediate next milestone:

```text
m2136-paper-route-outcome-supported-decisive-comparison-support-controlled-panel-result-audit
```

The continuation boundary:

```text
M2136 may audit M2134 only.
No ranking, paper-level claim, finite-window-vs-GRU conclusion, or level3
self-ID claim is admitted by this synthesis.
```
