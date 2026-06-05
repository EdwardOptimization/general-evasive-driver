# M2809 Engineering Controller Route A Post-Clearance Negative Non-Same-Repair Cross-Axis Bounded Execution Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- next branch decision: `pivot_to_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel_materialization`
- manifest: `experiments/manifests/m2809-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-result-synthesis.json`
- synthesis artifact: `docs/m2809-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-result-synthesis.md`
- parent audit: `docs/m2808-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-bounded-execution-result-audit.md`
- parent summary: `runs/m2807_engineering_controller_route_a_post_clearance_negative_non_same_repair_cross_axis_bounded_execution_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2810-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-localization-panel-materialization-preflight.json`
- next: `m2810-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-localization-panel-materialization-preflight`

## Evidence Summary

M2806-M2808 form a complete claim-safe Route A post-clearance
non-same-repair diagnostic branch.

M2806 changed the route away from the saturated same clearance-localized repair
loop. It admitted exactly 12 fixed M1690 `L3_online_gru` task-source rows that
do not overlap M2737, M2746, M2753, or the M2799/M2801 same-clearance repair
surface.

M2807 executed the selected surface with complete row accounting:

```text
candidate rows: 12
resolved candidates: 12
execution rows: 12
candidate execution failure rows: 0
stress-axis aggregate rows: 4
prior-surface exclusion rows: 37
unique prior task_source_ids: 21
blocker guard rows: 7
actor-contract guard rows: 12
claim-boundary rows: 15
gate rows: 21 all pass
```

M2808 accepted M2807 as complete and claim-safe while rejecting direct
interpretation.

The diagnostic outcomes are mixed but still weak:

```text
diagnostic success: 2/12
collision: 0/12
off_track: 10/12
termination counts:
  "": 2
  off_track: 10
```

This evidence differs from the earlier M2753/M2755 cross-axis branch. M2753 had
0/12 success, 3 collision, and 9 offtrack. M2807 has 2/12 success, no collision,
and 10 offtrack. That is a materially different diagnostic shape, but it is not
a solved driver or validation result.

Stress-axis aggregates are diagnostic context only:

```text
actuator_delay_or_response:
  episodes: 7
  diagnostic success rate: 0.0
  collision rate: 0.0
  offtrack rate: 1.0
  clearance_margin_mean: 5.89649837626962

capability_step_or_authority:
  episodes: 7
  diagnostic success rate: 0.14285714285714285
  collision rate: 0.0
  offtrack rate: 0.8571428571428571
  clearance_margin_mean: 8.550125500149669

late_boundary_or_near_boundary:
  episodes: 6
  diagnostic success rate: 0.3333333333333333
  collision rate: 0.0
  offtrack rate: 0.6666666666666666
  clearance_margin_mean: 5.347725712072408

curved_or_retargeted_obstacle:
  episodes: 2
  diagnostic success rate: 0.5
  collision rate: 0.0
  offtrack rate: 0.5
  clearance_margin_mean: 8.641016134778637
```

The branch therefore adds useful fresh Route A evidence, but it leaves the main
failure mechanism unresolved: the policy often avoids collision while going
off track. The next evidence-changing step is no-rollout localization of
offtrack containment rather than another execution or direct repair.

## Supported Claims

M2809 supports these bounded claims:

```text
M2806-M2808 form a complete claim-safe post-clearance non-same-repair Route A
diagnostic branch.

M2807 executed all 12 selected M1690 L3_online_gru task-source rows with 0
candidate accounting failures.

M2807 produced mixed weak diagnostic evidence: 2 success, 0 collision, and 10
off_track rows.

The branch preserved P0 observation shape 72 and action shape 3.

No hidden/oracle actor input was introduced.

Stress-axis, scenario-role, target, blocker, route-decision, success/progress,
and verdict labels remained actor-invisible.

M2737/M2746/M2753 prior surfaces, M2799/M2801 same-clearance repair rows,
protected mitigation rows, and HF3 blocker rows remained non-executed
guardrails outside ordinary success denominators.
```

These claims support only a bounded next-route decision. They do not support
repair success, validation readiness, driver performance, paper evidence,
current-sim or high-fidelity verdicts, full ideal driver completion, or level3
self-identification.

## Falsified Claims

M2809 rejects or fails to support:

```text
M2807 proves non-same-repair generalization success: false
M2807 proves repair success: false
M2807 proves driver performance: false
M2807 admits validation readiness: false
M2807 ranks stress axes, source families, task families, or profiles: false
M2807 selects a winner or promotes a checkpoint: false
M2807 resolves protected mitigation blocker: false
M2807 resolves HF3 source dependency blocker: false
M2807 provides paper finite-window-vs-GRU evidence: false
M2807 provides current-sim verdict evidence: false
M2807 provides high-fidelity validation evidence: false
M2807 provides full ideal driver completion or self-ID evidence: false
```

Another immediate M2807-like execution is also rejected. It would increase row
count before explaining why the same actor can pass two rows while failing ten
others through offtrack termination without collision.

Direct repair design is premature. The branch has not yet separated success
rows from noncollision offtrack rows, positive-clearance offtrack rows,
offtrack severity/time-to-offtrack, stress-axis context, task-family context,
and guardrail context.

## Failure Taxonomy Summary

Controlled:

```text
contract_violation:
  controlled. Actor observation/action contract remains 72/3 with no hidden or
  oracle actor input.

lineage_invalid:
  controlled. M2806 design, M2807 execution artifacts, M2808 audit, and the
  post-M2470 route plan are explicit.

proof_washout:
  controlled. Prior-surface, same-clearance repair, protected, and HF3 rows
  remain guardrails outside execution and ordinary denominators.

metric_artifact:
  controlled only if interpretation stays bounded. Positive clearance means
  with offtrack termination cannot be converted into success verdicts.
```

Active:

```text
scenario_sampling_failure:
  active caution. The selected non-same-repair surface produced 10/12 offtrack
  rows, so the branch is still diagnostic rather than validation-ready.

behavior_regression:
  active. The dominant failure is noncollision offtrack containment, not
  obstacle collision.

objective_overfit:
  active if the next route repeats non-same-repair execution or optimizes
  process completeness instead of explaining offtrack containment.

local_search:
  active if the branch returns to another same-clearance corrective update or
  another M2807-like surface without localization.

high_fidelity_dependency:
  active outside this branch. HF3 source dependency blockers remain unresolved
  and cannot be hidden by current-sim diagnostics.
```

## Public-Gate Overfit Risk

Risk is high if the next action is:

```text
another non-same-repair execution over similar M1690 rows
direct repair design from 2/12 diagnostic success
stress-axis aggregate ranking
success-rate verdict computation
claiming validation readiness from 0 collision rows
claiming driver performance from positive clearance means
claiming paper, current-sim, high-fidelity, full-driver, or self-ID evidence
```

Risk is lower if Route A materializes a no-rollout localization panel from the
existing M2807 rows. That panel can change the next admission decision by
separating:

```text
success obstacle-pass rows
offtrack noncollision rows
positive-clearance offtrack rows
offtrack severity and time-to-offtrack context
stress-axis context
task-family and source-edge context
prior-surface and same-clearance exclusion context
protected and HF3 blocker context
actor and claim boundaries
```

This preserves the `docs/post-m2470-route-plan.md` rule that current-sim work
must change the next admission decision rather than produce another static or
process-only loop.

## Next Branch Decision

M2809 chooses:

```text
pivot_to_post_clearance_negative_non_same_repair_offtrack_containment_localization_panel_materialization
```

Rejected alternatives:

```text
continue same non-same-repair execution:
  Rejected. M2807 already produced a complete weak diagnostic surface. Another
  similar run would not explain the offtrack containment mechanism.

direct repair design:
  Rejected as premature. The evidence must first distinguish success rows,
  noncollision offtrack rows, positive-clearance offtrack rows, and offtrack
  severity context.

validation or promotion:
  Forbidden. The branch has 10/12 offtrack rows and no validation gate.

package-with-limitations:
  Useful later, but it would not move Route A toward a better controller or
  better failure mechanism understanding right now.

defer-to-Route-B:
  Route B remains important, but this Route A branch has a concrete
  offtrack-containment mechanism question that can be localized without making
  a paper claim.

defer-to-Route-C:
  Route C remains important, but current M2807 artifacts can still be
  localized without running high-fidelity simulation or hiding HF3 blockers.
```

Admitted follow-up:

```text
m2810-engineering-controller-route-a-post-clearance-negative-non-same-repair-cross-axis-offtrack-containment-localization-panel-materialization-preflight
```

M2810 must be no-rollout materialization from existing M2807-M2809 artifacts.
It must write row-level localization, outcome bucket, offtrack containment,
stress-axis context, source-edge/task-family context, guardrail context,
actor-contract, claim-boundary, gate, summary, and milestone-doc artifacts. It
must not reset, step, run policy actions, rollout, replay, validate, train, run
PPO, source build, adapter probe, run external simulation, rank stress axes or
source edges, select a winner, promote a checkpoint, compute success-rate
verdicts, or make repair success, driver-performance, current-sim,
high-fidelity, full-driver, paper, or self-ID claims.

## Claim Boundary

Allowed M2809 claim:

```text
M2806-M2808 completed a claim-safe post-clearance non-same-repair diagnostic
branch, and its 2/12 success 0/12 collision 10/12 offtrack result requires
no-rollout offtrack-containment localization before any further execution,
repair, validation, ranking, or packaging claim.
```

Rejected claims:

```text
repair success
driver performance
validation readiness or result
controller-family ranking
source-family ranking
stress-axis ranking
task-family ranking
profile ranking
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
