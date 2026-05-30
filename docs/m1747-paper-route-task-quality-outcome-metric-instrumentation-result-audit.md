# M1747 Paper-Route Task-Quality Outcome Metric Instrumentation Result Audit

- status: completed
- decision: `metric_instrumentation_audit_route_to_branch_synthesis`
- audited implementation: `docs/m1746-paper-route-task-quality-outcome-metric-instrumentation-implementation.md`
- no rollout: true
- training/replay/PPO: false

## Summary

M1747 audits M1746 as a clean logging-only implementation. The implementation
adds outcome metric helper logic, evaluator episode-row fields, env `info`
diagnostic fields, and aggregate hooks without changing actor inputs, rewards,
dynamics, termination behavior, policy checkpoints, profile masks, training, or
promotion logic.

The audit does not admit immediate revised execution design. The
`paper_route_task_quality_scenario_taxonomy` branch has reached its 10-milestone
synthesis cadence from M1738 through M1747, so the next step is branch synthesis
before another narrow execution-design milestone.

## Evidence

Implementation evidence:

- helper module: `src/autodrift/outcome_metric_instrumentation.py`;
- evaluator metric fields: recovery, recovery time, controlled drift recovery,
  impact severity, collision mitigation score, off-track severity, and hidden
  dynamics aggregate support;
- logging-only env `info` fields: `yaw_rate`, `dt`, `track_width`;
- aggregate hooks: full rollout, bounded calibration smoke, and scenario
  taxonomy execution outputs.

Verification evidence:

```text
22 focused evaluator/outcome/full-rollout tests passed
11 affected aggregate/execution tests passed
1702 full test-suite tests passed, 4 warnings
research validation passed
```

## Guardrail Audit

| guardrail | status |
| --- | --- |
| actor input contract changed | false |
| reward changed | false |
| termination behavior changed | false |
| full 864-cell rollout started | false |
| training/replay/PPO used | false |
| checkpoint promoted | false |
| private holdout used | false |
| controller-family ranking claimed | false |
| paper-level evidence claimed | false |
| level3 self-ID claimed | false |

## Route Decision

Rejected route:

- immediate revised scenario execution design after M1746.

Reason: even though the implementation audit passes, the branch has reached the
workflow-synthesis cadence. Continuing directly would restart narrow rolling
without summarizing what M1738-M1747 established and what remains blocked.

Admitted route:

- M1748 paper-route task-quality scenario taxonomy branch synthesis.

M1748 should synthesize:

- repaired execution and outcome dominance evidence from M1738-M1741;
- revised semantics and materialization evidence from M1742-M1744;
- metric definition and logging instrumentation evidence from M1745-M1747;
- remaining risks before revised execution, including public-set overfit,
  off-track dominance, metric artifact risk, and self-ID claim boundaries.

## Claim Boundary

Supported:

- M1746 is logging-only and test-covered;
- revised execution design is technically unblocked by metric implementation;
- workflow cadence blocks direct continuation until synthesis.

Unsupported:

- revised rollout result;
- controller-family ranking;
- profile promotion;
- paper-level benchmark evidence;
- level3 self-identification.

## Decision

Route to M1748 branch synthesis before any revised scenario execution design.
