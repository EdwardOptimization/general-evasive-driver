# M1919 Executable V2 Task-Quality Scenario Redesign Plan

- status: completed
- decision: `task_quality_scenario_redesign_plan_admit_source_mining_design`
- branch: `paper_route_task_quality_scenario_redesign`
- parent synthesis: `docs/m1918-executable-v2-support-first-task-quality-repair-axis-measured-branch-synthesis.md`
- governing plans:
  - `docs/self-id-go-no-go-paper-route-plan.md`
  - `docs/paper-route-finite-window-vs-gru-plan.md`
- reset/rollout/measured execution in M1919: `false`
- training/replay/PPO: `false`
- controller-family ranking claim made: `false`
- paper-level claim made: `false`
- level3 self-ID claim made: `false`

## Problem

M1917 classified the complete measured repair-axis panel and found:

```text
joint_clearance_containment: 0 / 1536
clearance_only_offtrack: 1257 / 1536
containment_collision: 261 / 1536
collision_and_offtrack: 18 / 1536
near_miss_rows: 644 / 1536
```

This is not a controller-family result. It is a scenario/task-quality blocker:
the current fixed-source repair-axis panel mostly asks the controller to choose
between clearing the obstacle and staying on the road, without producing any
joint positive support.

The next branch must redesign scenario quality rather than continue local
repair-axis tweaking.

## Design Objectives

M1919 defines the next branch as a scenario-quality branch with five objectives:

1. Positive support:
   the task distribution must contain rows where joint obstacle clearance and
   road containment are possible before controller ranking is allowed.
2. Boundary value:
   the distribution must retain near-boundary and near-miss rows, because those
   are the cases that can later support finite-window/GRU/self-ID evidence.
3. Role coverage:
   stable AEB, stable AES, drift-required recovery, and unavoidable mitigation
   must remain separate role panels, not pooled into one success number.
4. Fresh sources:
   the branch must mine fresh source candidates instead of only repairing the
   current 16-source public panel.
5. Claim discipline:
   no controller ranking, paper-level claim, or level3 self-ID claim is allowed
   until scenario-quality gates pass.

## Feasibility Ladder

The redesigned scenario set should be built in tiers.

```text
Tier A: positive-support sanity
  Purpose: prove the instrumentation can produce joint clearance-containment.
  Expected: joint positives exist under benign timing/width/road settings.
  Claim allowed: task has positive support.

Tier B: feasible emergency
  Purpose: ordinary AEB/AES feasible cases with nonzero joint support.
  Expected: stable control can sometimes pass; not a ranking yet.
  Claim allowed: scenario family is not outcome saturated.

Tier C: boundary near-miss
  Purpose: cases near the clearance/containment boundary.
  Expected: mix of joint, clearance-only, containment-collision, near-miss.
  Claim allowed: usable task-quality boundary for later comparison.

Tier D: handling-limit / drift-required
  Purpose: hard cases where stable avoidance may be insufficient.
  Expected: joint support may be sparse but not structurally impossible.
  Claim allowed: candidate extreme-evasion benchmark rows.

Tier E: mitigation
  Purpose: unavoidable or near-unavoidable cases.
  Expected: success may be inappropriate; mitigation metrics dominate.
  Claim allowed: mitigation-only diagnostic panel, never mixed with success
  ranking.
```

## Positive-Support Gate

Before any controller-family comparison, a scenario pack must pass all of these
public diagnostic gates:

```text
row_count_target_met: true
sampling_failure_count: 0
guardrail_violation_count: 0
joint_clearance_containment_count > 0
joint support present in at least Tier A and Tier B
boundary near-miss rows present in Tier C or Tier D
mitigation rows isolated in Tier E
role panels reported separately
no controller-family ranking claim
```

Promotion toward controller comparison requires a stronger gate:

```text
joint_clearance_containment_rate is neither 0 nor saturated near 1
clearance_only_offtrack and containment_collision both appear
near_miss_rows are source-diverse
max single-source share is bounded
fresh-source split is recorded
private holdout remains unused for tuning
```

The exact numeric thresholds should be fixed in the materialization/preflight
manifest after source counts are known. The principle is invariant: ranking is
blocked until the task has positive support and a non-saturated boundary.

## Fresh-Source Policy

The branch should mine a new source corpus with explicit split metadata:

```text
public_debug:
  used for development, diagnostics, and failed-run repair

public_gate:
  used for routine gates and branch synthesis

paper_holdout_candidate:
  not used for local repair; only admitted after public gates stabilize
```

If a holdout row is used to repair a bug or tune scenario filters, it must be
rotated out and replaced. This keeps the eventual paper comparison from being a
long public-gate optimization.

## Scenario Axes

Source mining should vary:

- road width and post-obstacle recovery corridor;
- obstacle lateral offset and width;
- obstacle timing / reaction distance;
- initial speed;
- friction and friction-step timing;
- actuator delay / braking authority buckets;
- role panel and role surface;
- hidden-dynamics bucket;
- near-miss target class.

The first redesign wave should not add high-fidelity simulation. Current-sim
task quality must be repaired before Chrono/BeamNG-style validation becomes
useful.

## Actor And Controller Contract

This branch does not change actor inputs or outputs. The same non-negotiable
contract remains:

```text
allowed actor inputs:
  deployable ego response, actuator state, previous commands,
  road/free-space/obstacle geometry, finite-window or recurrent history

forbidden actor inputs:
  mu, mass, CG, tire stiffness, brake scale, actuator tau, slip, tire force,
  AEB/AES/drift labels, oracle feasibility, TTC, reference trajectory,
  path error, heading error, collision/success/progress answers

actor output:
  [steer, throttle, brake]
```

Scenario miners and diagnostics may use privileged simulator values only to
label or stratify artifacts. Those values must not enter deployable actor input.

## Stop Rules

The new branch must synthesize instead of continuing local search if any of
these happen:

- two consecutive source-mining/materialization waves still produce zero joint
  clearance-containment rows outside Tier E;
- a single source or role surface dominates the positive support;
- the only way to get positive support is to make the task trivial;
- controller ranking is requested before positive-support gates pass;
- another milestone would only tweak the same public sources or thresholds.

## Next

Next milestone:

```text
m1920-executable-v2-task-quality-scenario-redesign-source-mining-design
```

M1920 should design the source-mining artifact and exact acceptance gates for
the feasibility ladder. It should still not run reset, rollout, measured
execution, training, replay, PPO, controller ranking, paper-level claims, or
level3 self-ID claims.
