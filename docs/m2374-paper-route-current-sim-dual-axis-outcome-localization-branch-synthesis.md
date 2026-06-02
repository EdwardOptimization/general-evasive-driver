# M2374 Paper-Route Current-Sim Dual-Axis Outcome Localization Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_artifact_only_repair_plan_materialization`
- manifest: `experiments/manifests/m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis.json`
- synthesis artifact: `docs/m2374-paper-route-current-sim-dual-axis-outcome-localization-branch-synthesis.md`
- synthesis window: `M2364-M2373`
- reset/rollout/policy action in M2374: `false`
- measured execution in M2374: `false`
- repair execution/training/replay/PPO in M2374: `false`
- support-policy ranking claim made: `false`
- controller-family ranking claim made: `false`
- winner selected: `false`
- paper-level claim made: `false`
- finite-window vs GRU conclusion made: `false`
- level3 self-ID claim made: `false`
- scenario redesign executed claim made: `false`
- training repair success claim made: `false`

## Evidence Summary

M2364-M2373 turned the M2362 measured outcome panel into a bounded repair-route
artifact chain:

```text
M2364:
  designed artifact-only localization over the 5400-episode measured panel.

M2365:
  localized 313 measured outcome slices:
    offtrack targets 198
    collision guardrails 95
    R4 mitigation semantics 48
    high-priority offtrack 99

M2366:
  accepted localization and blocked raw ranking or paper interpretation.

M2367:
  designed consolidation of overlapping target and guardrail rows.

M2368:
  consolidated 313 source rows into:
    offtrack repair targets 54
    collision guardrails 28
    R4 mitigation semantics 48
    diagnostic guardrails 190
    diagnostic_axis_repair_target_count 0
    r4_ordinary_repair_target_count 0

M2369:
  accepted consolidation and routed to bounded offtrack guardrail repair
  design.

M2370:
  froze repair families and blocked actor input change, hidden/oracle
  features, profile-specific tuning, winner selection, R4 ordinary repair,
  collision-blind offtrack objectives, scenario-redesign-executed claims, and
  training-repair-success claims.

M2371:
  materialized 320 repair specs:
    priority offtrack 26
    ordinary offtrack 10
    mixed guarded offtrack 18
    collision guardrail 28
    R4 mitigation semantics 48
    diagnostic no-ranking guardrail 190
    guardrail_violation_count 0

M2372:
  accepted the repair-spec artifact and routed to implementation design.

M2373:
  designed artifact-only repair-plan materialization surfaces and routed to
  branch synthesis before another narrow materializer.
```

The branch obeyed the paper-route constraint: it repaired task-quality and
claim-boundary artifacts before any controller-family comparison, profile
ranking, finite-window-vs-GRU conclusion, or self-ID claim.

## Supported Claims

M2374 supports these bounded claims:

- The M2362 measured outcomes have been localized into actionable and
  diagnostic target surfaces.
- Diagnostic/profile/pack/global rows are no-ranking guardrails, not repair
  targets.
- R4 unavoidable mitigation semantics are separate from ordinary offtrack
  repair.
- Collision-heavy rows are guardrails or mixed guarded repair rows, not
  collision-blind offtrack objectives.
- A bounded artifact-only repair-plan materialization route is now specified.
- The branch reached a synthesis point before continuing local materialization
  work.

## Falsified Claims

M2374 blocks or falsifies these claims:

- The repair specs prove that a repair works.
- The scenario pack has already been redesigned.
- Training repair success has been demonstrated.
- Support policies or controller families can be ranked from these artifacts.
- Finite-window vs GRU can be concluded from this branch.
- Level3 self-identification evidence exists in this branch.
- More narrow repair-route milestones should continue without synthesis.

## Failure Taxonomy Summary

```text
scenario_sampling_failure:
  Still a live downstream risk. The branch has not run reset, rollout, or
  measured execution after repair-plan design.

metric_artifact:
  Reduced. R4 mitigation semantics, collision guardrails, diagnostic rows, and
  offtrack targets are now separated before repair planning.

contract_violation:
  No actor-input or hidden/oracle feature violation is present in M2364-M2373.

objective_overfit:
  Not tested. No training or reward objective was executed.

behavior_regression:
  Not tested. No policy behavior was changed or evaluated.

local_search_guard:
  Triggered correctly. The branch produced several artifact-only design,
  materialization, and audit milestones without new capability evidence, so
  synthesis is required before continuing.
```

## Public Gate Overfit Risk

The public gate overfit risk is moderate.

The branch uses the public M2362 measured panel and derives target/guardrail
surfaces from it. That is acceptable for task-quality repair planning, but it
cannot be used as paper-level performance evidence. The next route should
remain artifact-only until the repair plan is materialized and audited, then
any later execution should use explicit validation gates rather than direct
ranking or paper interpretation.

Risk controls preserved by M2364-M2373:

```text
no private holdout tuning
no active config overwrite
no profile/pack winner selection
no actor input change
no hidden/oracle feature injection
no repair execution or training claim
```

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new claim. No driver checkpoint is trained or evaluated.

mechanism evidence for history dependence:
  no new support. No wrong-history, reset-hidden, finite-window, or GRU
  comparison is run.

scenario/task-quality evidence:
  positive artifact evidence. The branch converted measured outcome failures
  into clean target, guardrail, repair-spec, and repair-plan design artifacts.

high-fidelity validation readiness:
  not ready. Current-sim repair plans have not been materialized, reset-tested,
  or measured.

workflow or complexity reduction:
  positive. The branch stopped before another local materializer and now has a
  synthesis-backed next route.
```

## Next Branch Decision

Decision:

```text
continue
```

Next branch:

```text
paper_route_current_sim_dual_axis_repair_plan_materialization
```

Next milestone:

```text
m2375-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization
```

M2375 should implement the artifact-only repair-plan materializer designed in
M2373. It should not execute repair. It should write:

```text
repair_implementation_plan.json
reward_delta_rows.csv
curriculum_weight_rows.csv
guardrail_constraint_rows.csv
mixed_guarded_constraint_rows.csv
claim_boundary.csv
summary.json
```

M2375 must keep all blocked routes blocked:

```text
reset/rollout/measured execution
repair execution
training/replay/PPO
actor input change
hidden/oracle feature injection
profile-specific tuning
ranking/winner selection
paper-level claim
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign executed
training repair success
```

## Blocked Routes

Blocked after synthesis:

```text
direct training from repair specs
direct scenario redesign execution
direct controller comparison
direct profile/pack/support-policy ranking
direct paper-route verdict
direct self-ID claim
another narrow outcome-localization branch milestone without the M2374
synthesis decision
```

## Claim Boundary

M2374 may claim only:

```text
The M2364-M2373 outcome-localization repair-route branch has been synthesized
and should continue to artifact-only repair-plan materialization.
```

Still blocked:

```text
repair execution
training repair success
scenario redesign executed
controller-family ranking
support-policy ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
current-sim verdict
```

## Next

Pre-registered follow-up:

```text
m2375-paper-route-current-sim-dual-axis-offtrack-guardrail-repair-plan-materialization
```
