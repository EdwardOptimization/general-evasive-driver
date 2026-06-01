# M2113 Paper-Route Outcome-Supported Decisive Public-Gate Core Measured Execution Branch Synthesis

- status: completed
- decision: `public_gate_core_measured_execution_synthesis_pivot_to_comparison_support_scenario_redesign`
- synthesis_decision: `pivot`
- reset/rollout/measured execution in M2113: `false`
- policy actions executed in M2113: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- finite-window vs GRU conclusion made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

M2106 continued the repaired public-gate core measured-execution branch after
metadata and seed repair. M2108 then proved the execution path:

```text
episode_count: 480 / 480
failure_count: 0
metadata_missing_count: 0
metric_completeness_failure_count: 0
guardrail_violation_count: 0
```

M2111 localized the complete M2108 artifact without rerun:

```text
outcome_counts_match_source_summary: true
success_row_count: 41
comparison_ready_candidate_count: 0
comparison_support_candidate_count: 0
collision_dominance_slice_count: 111
offtrack_dominance_slice_count: 1
guardrail_violation_count: 0
```

M2112 audited the localization result and blocked comparison readiness.

## Supported Claims

Supported:

```text
The public-gate core measured-execution infrastructure is repaired and can run
to completion with clean metadata and guardrails.
```

Also supported:

```text
The fixed public-gate smoke-proxy panel is not comparison-ready: localization
finds zero comparison-ready and zero candidate-support slices.
```

## Falsified Claims

Falsified or rejected:

```text
Aggregate profile rows from M2108 are sufficient for controller-family ranking.
```

Also rejected:

```text
Continuing same-panel local repair is the right next move.
```

The panel is useful for execution-infrastructure validation, but it has failed
as comparison evidence.

## Failure Taxonomy Summary

Structured failure type:

```text
promotion_gate_failure: the branch cannot promote to comparison/ranking because
comparison support is zero.
```

Secondary process risk:

```text
objective_overfit / public-gate overfit risk: the fixed smoke-proxy panel can
exercise execution infrastructure while still failing to produce meaningful
comparison support.
```

## Public-Gate Overfit Risk

Risk is high:

```text
the panel is fixed public-gate only;
all rows are generated smoke proxies;
there is no private holdout;
the outcome distribution is collision dominated;
no comparison-ready slice survives localization.
```

Therefore, the branch must not infer paper-level driver performance,
finite-window-vs-GRU conclusions, or self-identification evidence from this
panel.

## Next Branch Decision

Decision:

```text
pivot
```

Pivot to comparison-support scenario redesign. The next branch should design a
scenario distribution whose first objective is not harder task generation, but
measurable comparison support:

```text
enough successes for multiple profiles;
success diversity across sources;
collision and offtrack rates low enough for bounded comparison;
clear generated-proxy vs paper-valid claim boundary;
no direct controller ranking until support criteria pass.
```

Next milestone:

```text
m2114-paper-route-outcome-supported-decisive-comparison-support-scenario-redesign-design
```
