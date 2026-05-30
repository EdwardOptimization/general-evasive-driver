# M1748 Paper-Route Task-Quality Scenario Taxonomy Branch Synthesis

- status: completed
- synthesis decision: `continue`
- synthesized range: `M1738-M1747`
- no rollout: true
- training/replay/PPO: false

## Evidence Summary

M1738-M1747 turned the repaired scenario taxonomy from a runnable but
outcome-dominated public diagnostic workload into a semantics-aware,
metric-instrumented workload that is ready for revised execution design.

Key evidence:

- M1738 executed the repaired `72 x 12 = 864` public diagnostic matrix with
  zero execution failures, finite selected metrics, six scenario families, and
  clean guardrails.
- M1739 blocked raw interpretation because outcomes were dominated by
  non-success modes: `81` success obstacle passes, `279` collision failures, and
  `504` off-track noncollision noncompletions.
- M1740 localized that dominance as diffuse: `143` dominant slices across all
  `6` families and all `12` profiles.
- M1741 correctly rejected a narrow slice/profile repair and admitted
  family-specific outcome-semantics redesign.
- M1742 defined benchmark, diagnostic-stress, and mitigation-diagnostic roles
  with metric families for avoidance, controlled drift recovery, mitigation,
  boundary robustness, and hidden-dynamics robustness.
- M1743 materialized those semantics over the repaired taxonomy: `72` specs,
  `864` profile/spec cells, `432` benchmark cells, `288` diagnostic-stress
  cells, `144` mitigation-diagnostic cells, and `7` explicit metric gaps.
- M1744 blocked direct execution because recovery and controlled-drift metrics
  were benchmark-critical.
- M1745 designed bounded logging-only metric definitions.
- M1746 implemented the logging-only instrumentation and aggregate hooks.
- M1747 audited M1746 as logging-only and test-covered, then routed here because
  the synthesis cadence fired.

## Supported Claims

- The repaired scenario taxonomy is executable: the M1738 public matrix ran all
  `864` cells with zero execution failures.
- The unrevised outcome semantics were not benchmark-ready: off-track and
  collision dominance made raw success-rate comparison invalid.
- The correct repair was semantic and metric-oriented, not profile tuning.
- Revised scenario rows now have durable roles and primary metric families.
- The previously explicit metric gaps now have logging-only definitions and
  implementation hooks.
- The next technical step can be a revised public diagnostic execution design.

## Falsified Claims

- The M1738 raw aggregate can be used for controller-family ranking.
- A single off-track slice or one profile-specific repair is enough to fix task
  quality.
- Ordinary pass/fail success is sufficient for drift-required, unavoidable
  mitigation, boundary-stress, or hidden-dynamics stress families.
- Metric instrumentation can be skipped before revised execution.
- Any result in this branch is paper-level evidence or level3 self-ID evidence.

## Failure Taxonomy Summary

- `scenario_sampling_failure`: earlier M1731 sampling failure was repaired by
  M1734 and did not recur in M1738.
- `metric_artifact`: the main current risk. M1738 was executable but the raw
  outcome metric was semantically wrong for several families; M1742-M1746 fixed
  the definitions and logging route, but revised execution has not run yet.
- `public_gate_overfit`: remains material. The branch has repeatedly used public
  diagnostic artifacts; the next execution must remain diagnostic and cannot be
  reported as unbiased paper evidence.
- `contract_violation`: not observed. Actor inputs, rewards, termination
  behavior, and profile masks remain unchanged.

## Public Gate Overfit Risk

Risk: `moderate_high`.

Reasons:

- M1738-M1747 are all public diagnostic artifacts.
- The same 72-spec taxonomy has been inspected repeatedly.
- The implementation now makes the workload more measurable, but it does not
  create a private holdout or generalization benchmark.

Controls for the next route:

- no profile tuning;
- no controller-family ranking;
- no private-holdout claim;
- revised execution must be audited before interpretation;
- later paper evidence must use a fresh or rotated scenario distribution.

## Next Branch Decision

Decision: `continue`.

Continue within `paper_route_task_quality_scenario_taxonomy`, but only to
M1749 revised scenario execution design. M1749 should design a measured rerun
over the fixed semantics materialization and new logging-only metrics. It should
remain public diagnostic evidence and should route to execution only after the
design specifies metric completeness gates, aggregate artifacts, claim
boundaries, and no-ranking guardrails.

## Claim Boundary

Supported:

- branch synthesis and route decision;
- repaired taxonomy execution readiness;
- outcome semantics and metric instrumentation readiness for revised execution
  design.

Unsupported:

- revised execution result;
- controller-family ranking;
- profile promotion;
- private-holdout evidence;
- paper-level benchmark result;
- level3 self-identification.

## Decision

Route to M1749 revised scenario taxonomy execution design.
