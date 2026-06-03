# Post-M2470 Route Plan: stop current-sim drift and split the routes

## Purpose

This document records the route decision after M2470 and the external
ChatGPT-share review on 2026-06-03. It is a route/synthesis document, not a
milestone result. It does not complete M2471 and does not claim driver
performance, paper-level self-ID evidence, finite-window-vs-GRU evidence, or a
current-sim verdict.

The immediate reason for this document is that the current branch has spent too
long turning scenario-readiness blockers into more static infrastructure. That
work was necessary for evidence hygiene, but it is now close to becoming the
project's main loop.

## Current State

Live repo state at the time of writing:

```text
latest completed milestone:
  m2470-paper-route-current-sim-dual-axis-stable-aes-distribution-support-repair-design

active pending milestone:
  m2471-paper-route-current-sim-dual-axis-stable-aes-distribution-support-materialization-preflight
```

Relevant M2468-M2470 facts:

```text
M2468 distribution-support atlas:
  cells: 15
  reset-only attempts: 120
  reset successes: 109
  reset failures: 11
  stable_aes_support: 14/24
  stable-AES failures: 10/11 total reset failures

partial stable-AES cells:
  broad threshold-free: 5/8
  threshold-band: 3/8
  low-mu near: 6/8

M2470:
  status: completed
  type: design-only
  reset/rollout/policy action: false
  repair execution/training/ranking/winner/verdict: false
```

M2471 would only materialize three static stable-AES support rows:

```text
R1_AES_balanced_support
R1_AES_threshold_band_relief
R1_AES_low_mu_reaction_support
```

It explicitly would not reset the environment, execute policy action, run a
measured rollout, train, rank rows, select a winner, or make any paper,
self-ID, finite-window-vs-GRU, training-repair, or current-sim verdict claim.

## Problem

The current branch is no longer blocked by a missing controller idea. It is
blocked by scenario/readiness quality in the current simulator:

```text
scenario-quality discriminant
  -> concrete overlay design
  -> static/reset preflight
  -> reset-only validation
  -> R1 stable-AES seed-fragility diagnostic
  -> distribution-support atlas
  -> stable-AES support design
  -> pending static materialization
```

This is valid research bookkeeping, but it has three risks:

1. The project keeps producing infrastructure artifacts that cannot change the
   paper verdict.
2. The engineering controller route is being held hostage by current-sim
   readiness.
3. High-fidelity validation is delayed until current-sim is perfect, even
   though current-sim is only one diagnostic layer.

The controller project and the paper-proof project should now be separated
more explicitly.

## Route Decision

Pause M2471 as the immediate next action.

Do not continue directly into an M2471/M2472/M2473 chain of static
current-sim materialization and audit unless a new route-synthesis milestone
explicitly approves it.

Replace the immediate next action with a synthesis decision:

```text
m2471-current-sim-readiness-route-synthesis
```

The synthesis should answer:

```text
1. Did the recent M2452-M2470 branch change driver capability evidence?
2. Did it only improve scenario/readiness hygiene?
3. Is another current-sim static artifact likely to change the L0/L1/L2/L3
   comparison admission decision?
4. Is the branch overfitting public current-sim readiness gates?
5. Should current-sim be continued, capped, frozen as diagnostic, or bypassed
   for high-fidelity interface preparation?
```

Recommended synthesis decision:

```text
pivot_to_parallel_high_fidelity_interface_preparation
```

Current-sim should remain useful as a fast diagnostic and mining environment,
but it should stop blocking engineering and high-fidelity route preparation.

## Route A: Engineering Controller Mainline

Goal:

```text
freeze a usable actuator-level active-safety controller baseline
```

The engineering claim does not require strong self-ID:

```text
deployable actuator-level RL can perform emergency avoidance using human-view
ego response, actuator state, previous commands, and scene geometry
```

Near-term artifacts:

```text
baseline checkpoint list
actor input/output contract
public benchmark pack
known failure taxonomy
runtime/inference-cost report
scenario-role metric report
```

Allowed engineering claim:

```text
finite-window or current-response feedback may be sufficient for many active
safety tasks
```

Forbidden engineering shortcut:

```text
do not add hidden dynamics, oracle labels, slip/tire-force shortcuts, TTC,
reference trajectory, or precomputed success/progress signals to actor input
```

## Route B: Paper Evidence Mainline

Goal:

```text
make the L0/L1/L2/L3 comparison and self-ID claim falsifiable
```

The paper route should keep the existing claim ladder:

```text
L0: current-response adaptation
L1: history-conditioned control
L2: finite-window history advantage
L3: terminal-boundary self-ID
```

The fair comparison matrix remains:

```text
L0-current
L1-one-step
L2-finite-window: 0.25s, 0.5s, 1.0s, 2.0s
L2-current-tiled-control
L3-GRU
L3-reset/truncated-control
```

The paper route must not claim L3 from:

```text
aggregate success only
reset-only evidence
source-singleton positives
static materialization
single protected rows
current-sim scenario readiness artifacts
```

Acceptable outcomes:

```text
self-ID positive
self-ID negative
self-ID conditional
finite-window/current-feedback is the stronger engineering result
```

A negative or conditional self-ID result is still a valid paper route if it is
measured under a fair controller-family matrix.

## Route C: High-Fidelity Interface And Validation

Goal:

```text
prepare a validation layer without migrating the whole training loop too early
```

Start this route now in parallel with any bounded current-sim synthesis. Do not
wait for current-sim to become perfect.

Stage HF0: interface design only

```text
DynamicsBackend boundary
reset/step API mapping
time-step and actuator-latency contract
state extraction boundary
failure/status taxonomy
```

Stage HF1: P0 parity smoke

```text
P0 observation extractor
[steer, throttle, brake] action mapping
observation shape and value-range parity checks
no hidden/oracle actor inputs
```

Stage HF2: scenario taxonomy mapping

```text
stable avoidable / AEB-feasible
stable AES / AEB-infeasible
drift-required recovery
hidden-dynamics robustness
unavoidable mitigation
```

Stage HF3: low-cost pilot

```text
single-role stable avoidable pilot
single-role stable AES pilot
reset feasibility and rollout feasibility only
no controller-family verdict yet
```

Stage HF4: discrepancy report

```text
which current-sim failures reproduce
which disappear under higher fidelity
which new failures appear
whether current-sim remains a valid mining layer
```

Preferred platform direction remains an open, auditable high-fidelity vehicle
dynamics layer such as Chrono/Chrono::Vehicle, with black-box simulators only
as optional demonstration or industry-facing validation.

## Route D: Optional Horizon/K-Candidate Ablation

This is not the main route until the benchmark pack exists.

Use it as a diagnostic branch after the actuator-level baseline and scenario
roles are stable:

```text
single-step baseline
sequence-delta head, execute u0 only
K-candidate deterministic head
candidate selector or margin/recovery critic
```

The branch must preserve the deployed action contract:

```text
u_t = [steer_command, throttle_command, brake_command]
```

Do not use horizon-output as a shortcut around missing self-ID evidence,
scenario-readiness failures, or fair controller-family comparison.

## Hard Stop Conditions For Current-Sim Readiness Work

Current-sim readiness work may continue only under a bounded synthesis decision.
Stop or pivot if any of these are true:

```text
1. The next proposed task is another static design/materialization/audit that
   cannot change reset-readiness or controller-family admission.
2. Stable-AES reset-ready support is still partial after one bounded
   evidence-expanding attempt.
3. Measured rollout cannot be cleanly separated from sampler artifacts.
4. The branch starts ranking rows/cells/controllers before reset readiness is
   audited.
5. The branch changes the actor input contract to fix a scenario-readiness
   blocker.
6. The branch claims driver performance, L0/L1/L2/L3 evidence, self-ID, or
   current-sim verdict from reset-only or static artifacts.
```

The important local rule:

```text
no more static current-sim artifacts unless the synthesis proves the artifact
can change the next admission decision
```

## Immediate Next Tasks

Recommended replacement for pending M2471:

```text
1. Create m2471-current-sim-readiness-route-synthesis manifest.
2. Write the synthesis artifact that audits M2452-M2470 as a branch.
3. Decide between:
   - stop current-sim stable-AES micro-repair;
   - one bounded reset-readiness attempt;
   - freeze current-sim as diagnostic and pivot;
   - parallel high-fidelity interface preparation.
4. If pivot is selected, create the HF0 high-fidelity interface design
   manifest.
```

The recommended decision is:

```text
freeze current-sim as a diagnostic layer, allow at most one bounded
reset-readiness attempt, and start high-fidelity interface preparation now
```

## What This Document Does Not Do

This document does not:

```text
complete M2471
modify experiments/research_status.json
modify experiments/research_queue.csv
select a controller winner
claim current-sim benchmark readiness
claim finite-window-vs-GRU evidence
claim level-3 self-ID
claim engineering deployment readiness
```

It only records the route decision needed before spending more milestones on
current-sim support-materialization infrastructure.
