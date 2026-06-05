# M2739 Engineering Controller Route A Post-Negative Diagnostic Source-Diverse Bounded Execution Result Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization`
- manifest: `experiments/manifests/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.json`
- synthesis artifact: `docs/m2739-engineering-controller-route-a-post-negative-diagnostic-source-diverse-bounded-execution-result-synthesis.md`
- parent audit: `docs/m2738-engineering-controller-route-a-post-negative-diagnostic-source-diverse-closed-loop-evidence-surface-bounded-execution-result-audit.md`
- parent summary: `runs/m2737_engineering_controller_route_a_post_negative_diagnostic_source_diverse_closed_loop_evidence_surface_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight.json`
- next: `m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight`

## Evidence Summary

M2731-M2738 refreshed Route A after the negative exact-executable repair loop.
The branch moved from evidence indexing to a source-diverse diagnostic surface,
then executed a bounded closed-loop preflight and audited it before
interpretation:

```text
M2731 evidence index:
  evidence rows: 10
  blocker rows: 5
  next-action admission rows: 6
  accepted route: M2733 source-diverse evidence-surface design

M2734 evidence-surface materialization:
  input source rows: 6
  candidate rows: 18
  source-diversity buckets: 2
  negative-context rows: 31
  blocked rows: 12
  actor guards: 10
  gate rows: 26

M2737 bounded diagnostic execution:
  status_pass: true
  candidate rows resolved and executed: 18/18
  execution failure rows: 0
  source-family aggregate rows: 2
  task-family aggregate rows: 2
  negative-context guard rows: 31
  blocked-surface guard rows: 12
  actor-contract guard rows: 13
  claim-boundary rows: 35
  gate rows: 21
```

The M2737 outcome is useful diagnostic data, but it is weak and
offtrack-dominated:

```text
overall outcome:
  success_obstacle_pass: 3/18
  collision_failure: 1/18
  off_track_noncollision_noncompletion: 14/18

source-family outcome:
  M2693 source_diverse_current_sim_offtrack: 1 success, 1 collision, 7 offtrack
  M2716 exact_executable_reentry_baseline: 2 success, 0 collision, 7 offtrack

task-family outcome:
  T4: 1 success, 0 collision, 9 offtrack
  T5: 2 success, 1 collision, 5 offtrack
```

The row-level signal is also directional enough to justify a taxonomy surface
before any new execution. The offtrack rows include early noncollision
containment losses across both source families, while the single collision row
is a T5 drive-loss and curved-boundary obstacle case with negative clearance
margin. The three success rows remain context rows, not a success-rate verdict.

The guardrail surface remains intact:

```text
M2728 negative context rows: 31, not executed by M2737
blocked rows: 12, not executed by M2737
blocked families: same_surface_repair_loop, protected_mitigation_blocker,
  hf3_source_dependency_blocker
protected rows in success denominator: false
actor observation shape: 72
action shape: 3
hidden/oracle actor input detected: false
actor-visible labels or verdicts: false
```

The post-M2470 route plan warns against more static or same-surface
current-sim work that cannot change admission or evidence boundaries. M2737
did change the evidence state by adding source-diverse closed-loop rows, but
another immediate M2737-like execution would be local search. The next bounded
step should convert the weak closed-loop evidence into a row-level failure
taxonomy and scenario-role metric surface.

## Supported Claims

M2739 supports these limited claims:

```text
M2731-M2738 form a complete post-negative Route A diagnostic branch.

M2737 produced complete and claim-safe bounded source-diverse closed-loop
diagnostic execution rows after M2734 materialization and M2736 design.

The branch preserved the actor P0 contract: observation shape 72, action shape
3, no hidden/oracle actor input, no actor-visible target, taxonomy, protected,
blocker, source-family, task-family, route, progress, success, or verdict
labels.

M2728 negative context rows, same-surface repair rows, protected blocker rows,
and HF3 blocker rows remained guardrails outside M2737 execution and outside
ordinary success denominators.

M2737 is strong enough to justify no-rollout failure taxonomy materialization:
14 offtrack rows, 1 collision row, 3 success context rows, two source families,
two task families, and explicit guardrail rows can be preserved in a new
taxonomy artifact.
```

## Falsified Claims

M2739 rejects these interpretations:

```text
M2737 proves repair success.
M2737 proves driver performance.
M2737 proves validation readiness or a validation result.
M2737 ranks source families, task families, profiles, or controller families.
M2737 selects a winner or promotes a checkpoint.
M2737 proves a current-sim verdict.
M2737 proves high-fidelity validation readiness or a high-fidelity result.
M2737 proves paper evidence, finite-window-vs-GRU evidence, full ideal driver
completion, or level3 self-identification.
```

M2739 also rejects another immediate source-diverse execution over the same
surface. The current branch has already designed, materialized, executed, and
audited that surface. Repeating it before taxonomy would mostly increase row
count without changing the evidence question.

## Failure Taxonomy Summary

- `contract_violation`: not observed. The P0 actor contract and label
  invisibility boundaries remain intact.
- `lineage_invalid`: not observed. The branch traces from M2731 evidence index
  through M2734 materialization, M2736 design, M2737 execution, and M2738 audit.
- `metric_artifact`: controlled. Source-family and task-family aggregates are
  diagnostic only and non-ranking.
- `scenario_sampling_failure`: active. Both source families remain
  offtrack-dominated and T4 is 9/10 offtrack.
- `behavior_regression`: active as caution, not as proof. The single collision
  row is T5 drive-loss and curved-boundary obstacle context; it must stay
  visible in taxonomy before any repair or benchmark route.
- `objective_overfit`: medium-high if the branch runs another similar public
  source-diverse execution; controlled by moving to no-rollout failure taxonomy
  and then auditing before repair or validation.
- `proof_washout`: controlled. M2739 explicitly rejects performance,
  validation, paper, current-sim, high-fidelity, full-driver, and self-ID
  claims from M2737.

## Public Gate Overfit Risk

Risk entering M2739: `medium-high`.

Reason:

```text
M2731-M2738 correctly left the failed same-surface repair loop, but the branch
has now spent several milestones on one source-diverse current-sim diagnostic
surface. The result is mostly offtrack and does not justify another execution
until the row-level failure modes are made explicit.
```

Risk after M2739: `medium` only if the next step is no-rollout taxonomy
materialization and result audit. Risk stays high if the branch immediately
executes another current-M1690 source-diverse panel, ranks families, or
rebrands diagnostic rates as performance.

Route constraints:

```text
Do not schedule another M2737-like execution before taxonomy and audit.
Do not rank M2693 versus M2716 from the aggregate rows.
Do not treat T4/T5 rates as a task-family verdict.
Do not execute M2728 same-surface repair rows or protected/HF3 blockers.
Do not claim Route B paper evidence or Route C high-fidelity readiness.
Keep current-sim as diagnostic rather than as the final verdict layer.
```

## Next Branch Decision

Decision:

```text
continue_to_route_a_post_negative_diagnostic_source_diverse_failure_taxonomy_materialization
```

The next bounded route is:

```text
m2740-engineering-controller-route-a-post-negative-diagnostic-source-diverse-failure-taxonomy-materialization-preflight
```

M2740 should materialize no-rollout taxonomy rows from the accepted M2737
execution artifacts and guardrail rows. It should preserve:

```text
18 M2737 execution rows
14 offtrack rows
1 collision row
3 diagnostic success context rows
2 source families
2 task families
31 M2728 negative-context guard rows
12 blocked guard rows
actor 72/action 3
no hidden/oracle actor input
all taxonomy and verdict labels actor-invisible
```

M2740 must not reset environments, step environments, run policy actions,
rollout, replay, validate, train, run PPO, build external sources, probe
adapters, rank rows, select a winner, promote a checkpoint, or claim repair,
performance, validation, paper, current-sim, high-fidelity, full ideal driver,
or self-ID evidence.

Rationale:

```text
Stopping the whole project is wrong because the full ideal driver gate has not
passed.

Direct validation or performance interpretation is forbidden because M2737 is
offtrack-dominated and diagnostic-only.

Another immediate execution is local search because it would repeat the same
source-diverse surface without a new evidence question.

Failure taxonomy materialization changes the evidence surface by turning weak
closed-loop rows into explicit offtrack, collision, success-context, source,
task, and guardrail categories for later audit, controller design, route-A
baseline reporting, or a bounded pivot.
```
