# Active Safety Driver v1 Route Plan

## Purpose

This document records the route pivot after the 2026-06-07 ChatGPT-share
review and the live M3032/M3033 repository state. It is a route plan, not a
driver-performance result. It does not claim repair success, current-sim
verdict, high-fidelity validation, finite-window-vs-GRU evidence, paper-level
self-ID evidence, or full active-safety-driver completion.

The project goal is now:

```text
Build and validate an actuator-level active-safety reflex driver.
```

The driver should act in hazard windows using deployable vehicle feedback,
environment geometry, and action-response history, and output:

```text
[steer, throttle, brake]
```

Self-ID, GRU belief, finite-window history, horizon-output, and K-candidate
heads are implementation candidates or diagnostics. They are not the project
objective and must not block the engineering mainline indefinitely.

## Current State

Live repository state at the time of writing:

```text
latest completed milestone:
  m3032-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-preflight

active pending milestone before this pivot:
  m3033-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-tensor-materialization-result-audit
```

M3032 materialized a claim-safe target tensor panel:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
candidate target tensor rows: 29
success identity zero-target guard rows: 3
target tensor files: 32
target_action_delta_abs_max: 0.08
actor observation/action: 72/action 3
local-action search: false
environment step: false
fitting/training/validation/ranking/checkpoint mutation: false
```

This is useful offline material. It is not fitting readiness, repair success,
driver performance, high-fidelity evidence, finite-window-vs-GRU evidence, or
self-ID evidence.

## Problem

The recent Route A branch has repeatedly produced correct artifacts while
deferring the actual engineering question:

```text
Does any deployable actuator-level controller reduce active-safety failures?
```

The project should stop treating these as primary blockers:

```text
GRU self-ID proof
paper-grade wrong-history source diversity
single historical proof rows
target tensor artifact chains
static current-sim readiness bookkeeping
process-only audit/materialization loops
```

They remain useful diagnostics, but they cannot be allowed to define success
for an engineering active-safety driver.

## Route Decision

Accept M3032 as complete and claim-safe. Do not continue directly into residual
fitting or target tensor quality claims.

Pivot to:

```text
m3034-engineering-controller-active-safety-driver-v1-baseline-freeze-design
```

The new branch is:

```text
active_safety_driver_v1_engineering_mainline
```

The next route should freeze a usable engineering baseline and benchmark
surface before training, architecture changes, horizon-output, K-candidate
heads, or high-fidelity validation.

Recommended decision:

```text
pivot_to_active_safety_driver_v1_baseline_freeze_design
```

## Engineering Objective

Define Active Safety Driver v1 as:

```text
Input:
  P0 human-view ego response
  actuator state
  previous commands
  road and obstacle geometry
  optional deployable history through finite-window or recurrent state

Output:
  [steer, throttle, brake]

Primary metric families:
  collision rate
  off-track rate
  minimum clearance p5/p10
  yaw stability / spin rate
  recovery time
  control smoothness
  low-grip / delay / brake-authority robustness
  unavoidable mitigation severity
```

Forbidden actor shortcuts remain:

```text
hidden dynamics
mu
slip ratio
tire force
oracle feasibility
TTC labels
reference trajectory
precomputed success/progress/verdict labels
target tensor labels or provenance
```

## Phase A: Baseline Freeze

Goal:

```text
produce the official current-sim engineering baseline table
```

Required artifacts:

```text
candidate checkpoint list
actor input/output contract
active-safety benchmark roles
baseline outcome table
known failure taxonomy
runtime / inference-cost report
guardrail list
```

The first table should answer:

```text
What does the parent driver actually do?
Which failures dominate: collision, off-track, spin, speed-too-low, max-step?
Which task roles are currently measurable enough for engineering comparison?
Which rows are excluded as stale/static/diagnostic-only?
```

No training should happen before this freeze.

## Phase B: Engineering Training

Training objectives should be engineering objectives, not self-ID objectives:

```text
collision penalty
off-track penalty
minimum-clearance reward
yaw/spin stability penalty
recovery reward
control smoothness
steer/throttle/brake actuator regularization
low-grip and actuator-delay robustness
```

If PPO is used, gates should be simplified to engineering gates:

```text
actor contract unchanged
behavior not worse
collision not worse
off-track not worse
fresh/OOD not worse
no catastrophic rollback
no checkpoint promotion without benchmark evidence
```

Legacy self-ID proof gates can be reported, but they should not veto all
engineering progress unless they expose a direct safety regression.

## Phase C: Architecture Selection

The architecture question is:

```text
Which controller family produces safer active-safety behavior?
```

Compare:

```text
L0 current-only
L1 one-step feedback
L2 finite-window 0.5s / 1.0s / 2.0s
L3 GRU
```

Allowed outcomes:

```text
finite-window is sufficient
GRU helps only under delay/noise/history-necessary tasks
GRU is not supported as mainline
current-response is strongest on the current benchmark
```

Any of these outcomes is valid if supported by same-case engineering metrics.

## Phase D: Horizon And K-Candidate Ablations

Treat horizon-output and K-candidate action heads as controlled ablations:

```text
single-step actor
sequence-delta head, execute u0 only
K action candidates
K sequence candidates
learned safety selector
margin / recovery critic selector
```

Do not mainline any of these unless they improve active-safety metrics without
creating selection instability, mode jumps, actor-contract violations, or
unacceptable runtime cost.

## Phase E: High-Fidelity Validation Layer

High-fidelity simulation should start as a validation layer, not as a training
loop replacement.

Stages:

```text
HF0: Chrono or lightweight four-wheel backend source/package decision
HF1: backend build/import/reset
HF2: P0 observation and action mapping
HF3: manual action step
HF4: one-episode policy smoke
HF5: active-safety small benchmark
HF6: actuator-output vs acceleration-output and finite-window vs GRU sanity
```

If Chrono dependencies remain unavailable, pivot to an auditable lightweight
four-wheel backend instead of spending more milestones on missing dependency
bookkeeping.

## Stop Rules

Stop or pivot a branch if:

```text
1. It produces only static artifacts and no possible driver-metric delta.
2. It needs more than two process milestones before an evidence-changing run.
3. It tries to prove universal GRU self-ID before measuring engineering safety.
4. It turns target tensors into fitting readiness without audit and validation.
5. It changes actor inputs to include hidden/oracle/diagnostic shortcuts.
6. It blocks high-fidelity interface preparation on current-sim perfection.
```

## Immediate Next Tasks

Replace the post-M3032 direct fitting route with:

```text
1. Complete M3033 as a pivot audit.
2. Register M3034 active-safety-driver-v1 baseline freeze design.
3. In M3034, define the benchmark roles, baseline checkpoint list, metrics,
   exclusion rules, and hard stop conditions.
4. Only after the baseline table exists, choose one engineering training or
   architecture-comparison milestone.
```

This route keeps M3032 target tensors available as offline material but stops
them from driving the mainline.
