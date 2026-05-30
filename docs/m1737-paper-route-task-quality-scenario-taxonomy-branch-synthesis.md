# M1737 Paper-Route Task-Quality Scenario Taxonomy Branch Synthesis

- status: completed
- workflow synthesis decision: `continue`
- decision: `continue_to_repaired_scenario_taxonomy_execution`
- synthesized range: M1727-M1736
- parent design: `docs/m1736-paper-route-task-quality-repaired-scenario-taxonomy-execution-design.md`

## Evidence Summary

M1727-M1736 moved the task-quality scenario taxonomy branch from design through
a failed unrepaired execution and into a repaired execution-ready state:

- M1727 designed a six-family scenario taxonomy: ordinary stable avoidance,
  AEB-infeasible stable AES, drift-required avoidance, unavoidable mitigation,
  off-track boundary stress, and hidden-dynamics stress.
- M1728 materialized the taxonomy as no-rollout metadata: `72` specs, `864`
  profile cells, `12` profiles, zero contract violations, and `5` explicitly
  unsupported fault-like features.
- M1729 audited the no-rollout preflight as clean and required metadata joins
  for measured execution.
- M1730 designed the unrepaired execution.
- M1731 implemented the runner and exposed the real blocker: `422/864`
  completed episodes and `442` reset-time sampling failures.
- M1732 audited that as `scenario_sampling_failure`, not policy behavior,
  replay, PPO, or self-ID evidence.
- M1733 designed a non-mutating sampling repair route with reset-stress
  feasibility before policy rollout.
- M1734 materialized repaired artifacts and passed reset-only feasibility:
  `864/864` reset successes, `0` sampling failures, `0` contract violations.
- M1735 audited M1734 as clean sampling-feasibility evidence, while blocking
  performance/ranking claims from reset-only rows.
- M1736 designed repaired measured execution with repair provenance and
  sampled-label aggregates.

The branch corrected an important workflow gap: no-rollout metadata preflight is
not enough for scenario execution readiness. Reset-stress feasibility is now a
required intermediate gate when label/filter sampling is tight.

## Supported Claims

- The six-family taxonomy is materially defined and traceable.
- Unsupported fault-like features remain explicitly not covered.
- M1731 identified a real scenario sampling failure before policy evaluation.
- M1734 repaired that reset-time failure without mutating M1728 artifacts in
  place and without actor/profile/checkpoint changes.
- The repaired taxonomy is ready for a measured public diagnostic execution
  attempt.

## Falsified Claims

- M1728 no-rollout metadata preflight alone was not sufficient to admit policy
  execution.
- The unrepaired M1728 taxonomy was not execution-ready.
- M1734 reset-only rows are not controller-family performance evidence.
- The branch is not ready for controller-family ranking, paper-level benchmark
  claims, recurrent advantage claims, or level3 self-identification claims.

## Failure Taxonomy Summary

Observed failure:

```text
scenario_sampling_failure
```

The failure was localized to reset-time obstacle scenario sampling and repaired
by M1734. No evidence in this branch supports these failure types:

```text
proof_washout
behavior_regression
training_instability
contract_violation
private_holdout_contamination
```

Remaining risks:

```text
public_gate_overfit_risk: moderate
scenario_task_quality_risk: high until M1738 execution/audit exists
metric_artifact_risk: moderate
self_id_overclaim_risk: high if profile controls are ranked prematurely
```

## Public-Gate Overfit Risk

Risk is still `moderate`.

Reasons:

- The repaired taxonomy was tuned against public M1731 failure rows.
- The reset-stress pass proves feasibility, not task-quality realism.
- The next execution will still be public diagnostic evidence.
- Controller-family profile rows must remain controls until a later audit
  defines a fair comparison rule.

This risk is acceptable for one repaired execution because M1734 explicitly
records repair deltas and label distributions, and M1738 interpretation will be
deferred to a result audit.

## Next Branch Decision

Decision:

```text
continue_to_repaired_scenario_taxonomy_execution
```

Continue the same branch, with the synthesis counter reset:

```text
paper_route_task_quality_scenario_taxonomy
```

Next milestone:

```text
m1738-paper-route-task-quality-repaired-scenario-taxonomy-execution
```

M1738 should execute the M1734 repaired `864`-cell matrix and preserve repair
provenance, sampled labels, scenario metadata, and unsupported-feature
boundaries. M1738 itself may only claim execution completion; task-quality
interpretation must be deferred to a follow-up audit.

## Claim Boundary

Allowed:

```text
scenario taxonomy branch synthesis;
sampling failure repaired at reset-stress level;
route decision toward repaired public diagnostic execution.
```

Forbidden:

```text
controller-family ranking;
scenario-family task-quality conclusion before repaired execution audit;
finite-window history necessity;
recurrent advantage;
private-holdout evidence;
paper-level evidence;
level3 self-identification.
```
