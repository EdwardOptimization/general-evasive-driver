# M2283 Paper-Route Current-Sim Scenario/Task-Quality Redesign Branch Synthesis

- status: completed
- synthesis decision: `continue`
- manifest: `experiments/manifests/m2283-paper-route-current-sim-scenario-task-quality-redesign-branch-synthesis.json`
- synthesis artifact: `docs/m2283-paper-route-current-sim-scenario-task-quality-redesign-branch-synthesis.md`
- synthesis window: `M2273-M2282`
- reset execution in M2283: `false`
- rollout/measured execution in M2283: `false`
- policy actions executed in M2283: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Evidence Summary

This branch asked whether the current-sim route could stop optimizing scalar
reward/local outcome slices and instead create a role-supported scenario pack
that can later support fair controller-family comparison.

The main evidence is:

```text
M2273:
  Defined six role-specific current-sim task families:
  R0 stable avoidable, R1 AEB-infeasible stable AES, R2 handling-limit/drift-capable
  avoidance, R3 recovery-after-limit, R4 unavoidable mitigation, and R5 hidden
  dynamics robustness. It also blocked ranking/training until role and axis
  support were explicit.

M2274-M2275:
  Artifact-only support audit over 1440 episode rows and 60 training-matrix rows
  passed cleanly, but found incomplete role/scenario support. Explicit role
  family support was only 3/6, R1 was missing in the provisional mapping, R3/R5
  were proxy-only, and direct timing/lateral axes were missing.

M2276:
  Corrected the role mapping:
    aeb_feasible -> R0_stable_avoidable
    aes_feasible -> R1_aeb_infeasible_stable_aes
  and froze a no-reset 72-spec role-family generation design.

M2277-M2278:
  Materialized 6 role families and 72 specs with metadata missing 0, duplicate ids
  0, labels entering actor input 0, actor contract violations 0, ranking rows 0,
  and guardrail 0. However, 38 left/right lateral-offset specs were execution
  blockers because emergency obstacle placement was centerline-only.

M2279-M2281:
  Designed and implemented `obstacle.lateral_offset_range`, preserving default
  centerline behavior and P0 observation shape 72. The materializer refresh
  reduced unsupported execution blockers from 38 to 0 and M2281 audited the
  result as guardrail clean.

M2282:
  Froze a focused reset-validation design over the 72-spec pack, including
  contract checks, label consistency checks, and lateral-offset numeric/bucket
  sign checks. M2282 also identified a likely sign-convention risk: the current
  materializer appears to map `left_offset -> -1.2` and `right_offset -> +1.2`,
  while instrumentation semantics define positive offset as frame-left.
```

## Supported Claims

- The branch successfully moved the current-sim paper route away from another
  scalar reward tweak and toward explicit role-specific scenario/task quality.
- A 72-spec v0 scenario pack now exists with six role families and clean
  no-reset materialization metadata.
- The P0 actor contract stayed intact: no hidden parameters, role labels,
  feasibility labels, ranking labels, wheel/slip state, or privileged values
  enter the actor input.
- The emergency obstacle lateral-offset instrumentation exists and cleared the
  previous current-sim execution blocker count.
- Reset-validation gates are now explicitly designed and include label and
  signed lateral-offset consistency checks.
- The branch improves scenario/task-quality evidence and workflow discipline.

## Falsified Claims

- Falsified: existing old episode rows alone are enough for a role-supported
  paper-route benchmark pack.
- Falsified: lateral offset diversity can be safely represented while the
  obstacle task remains centerline-only.
- Not proven: the 72-spec pack is reset-valid. M2282 is design-only.
- Not proven: left/right bucket names match the new signed lateral-offset
  semantics. This is now an explicit M2284 gate.
- Not proven: the task pack supports controller-family ranking, finite-window vs
  GRU conclusions, paper-level benchmark claims, or level3 self-identification.

## Failure Taxonomy Summary

Primary failures handled in this branch:

```text
scenario_sampling_failure
contract_violation
metric_artifact
```

Interpretation:

- `scenario_sampling_failure`: the prior task mix lacked explicit role families
  and direct timing/lateral axes. The new pack addresses this at materialization
  level, but reset validity is still untested.
- `contract_violation`: no current violation is present, but every next step
  must continue to check P0 human-view/no-oracle inputs.
- `metric_artifact`: controller ranking and paper claims remain blocked because
  no reset, rollout, or measured execution evidence exists for the new pack.

New risk exposed:

```text
lateral_offset_metadata_inconsistency
```

This is represented under the allowed process taxonomy as
`scenario_sampling_failure` until M2284 produces reset rows and M2285 audits the
failure mode.

## Public Gate Overfit Risk

Risk is medium-low for policy overfit because this branch does not optimize a
checkpoint or tune against fixed replay rows. The main risk is process overhead:
many milestones were needed to move from support audit to a reset-validation
design.

The M2282 lateral sign gate is a useful anti-overfit constraint. It prevents the
branch from treating "72 specs materialized" as sufficient when the semantics of
left/right obstacle placement may be wrong.

## Paper-Route Axis Classification

```text
engineering driver performance:
  no new support. No policy actions, rollout, training, or measured execution
  were run in M2273-M2282.

mechanism evidence for history dependence:
  no new support. No wrong-history, reset-hidden, finite-window, or GRU
  comparison test was run.

scenario/task-quality evidence:
  positive but incomplete. The branch now has a role-family scenario pack and
  cleared the lateral-offset instrumentation blocker, but reset validation has
  not yet run.

high-fidelity validation readiness:
  not ready. Current-sim reset validation and later measured execution must
  come first.

workflow or complexity reduction:
  positive. The branch inserted cadence synthesis before implementation and
  made the next gate fail-closed instead of silently repairing metadata.
```

## Governing Plan Consistency

The synthesis remains consistent with the paper-route plans:

```text
self-ID and GRU belief remain bounded hypotheses, not assumptions;
finite-window vs GRU ranking remains blocked;
role-specific current-sim task quality must precede controller-family ranking;
reset-only evidence cannot support paper-level driver performance;
source-singleton or reset-only evidence cannot support level3 self-ID.
```

## Next Branch Decision

Decision:

```text
continue
```

The next milestone should implement the frozen reset-validation runner:

```text
m2284-paper-route-current-sim-scenario-task-family-reset-validation-implementation
```

M2284 should run only reset validation over:

```text
configs/paper_route_current_sim_scenario_task_family_v0.json
```

with the M2282 pass gates. It must fail closed on any reset failure,
actor-contract violation, label mismatch, or lateral-offset sign/bucket
mismatch. It must not repair materialization and rerun inside the same
milestone.

If M2284 fails because left/right buckets are sign-inconsistent, M2285 should
route to materialization repair. If M2284 passes, M2285 can audit reset validity
and then decide whether measured-execution design is admissible.

## Blocked Claims

Still blocked:

```text
rollout success
measured execution success
training result
controller-family ranking
winner selection
finite-window-vs-GRU verdict
paper-level result
level3 self-identification
high-fidelity validation as a replacement for current-sim reset validation
```
