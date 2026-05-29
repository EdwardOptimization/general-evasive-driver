# Self-ID Go/No-Go Paper Route Plan

## Purpose

This plan turns self-identification from an assumed project thesis into a
bounded, falsifiable research hypothesis. The project should still build a
deployable actuator-level evasive driver, but it should no longer assume that
GRU recurrent belief is the final engineering answer.

The route must produce a complete paper whether self-ID is:

- positive: recurrent history adds source-diverse terminal-boundary value;
- negative: current-response or finite-window feedback is sufficient;
- conditional: recurrent history helps only in delayed, ambiguous, or
  terminal-boundary tasks.

## Current Position

The live project is on the paper route. Recent work has built staged warmup,
source-step geometry, source-diverse pressure, and neighbor-viability
calibration infrastructure. The current public base remains the deployable P0
human-view no-wheel actor family, and the current near-term blocker is to
validate calibrated neighbor candidates before another replay attempt.

The latest source-diverse pressure replay produced history-positive signal, but
the positives were still source-singleton. That is enough to continue scenario
calibration, but not enough for a paper-level self-ID claim.

## Non-Negotiable Controller Contract

The deployable actor may use:

- ego kinematics and IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road, free-space, and obstacle geometry in ego frame;
- explicit finite-window history or recurrent hidden state.

The deployable actor must not use:

- hidden dynamics parameters such as `mu`, mass, CG, tire stiffness, brake
  scale, or actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, or friction margin;
- AEB/AES/drift-required labels, oracle feasibility, controller mode, TTC,
  reference trajectory, path error, heading error, or required clearance;
- collision, success, progress, or any precomputed answer.

Training-time diagnostics, teachers, miners, and evaluation may use privileged
state, but those values must never enter actor input.

## Claim Ladder

Use the weakest claim supported by evidence.

```text
L0: current-response adaptation
    The controller reacts using current ego response, actuator state,
    previous command, and scene geometry.

L1: history-conditioned control
    Recent command-response history improves prediction, first-critical action,
    or terminal margin beyond current response.

L2: recurrent or finite-window history advantage
    Multi-step history is useful, but GRU may only be one implementation.

L3: terminal-boundary self-ID
    Correct history improves near-boundary outcome while wrong, stale,
    delayed, reset, or mismatched history degrades the maneuver.
```

Do not claim L3 from aggregate success, reset-hidden-only tests, or
source-singleton proof rows.

## Stage I: Current-Simulator Go/No-Go

### Step 1: Finish Calibrated Candidate Validation

Complete the current calibrated neighbor route in order:

```text
proposal generation
  -> source-step preflight
  -> bounded replay
  -> replay audit
  -> branch synthesis
```

The route may continue only if calibrated candidates remain source-step
anchored, geometry-valid, duplicate-key clean, and source-diverse.

### Step 2: L0/L1/L2/L3 Fair Controller Matrix

Compare these controller families under the same action contract:

```text
L0-current:
  current deployable observation only.

L1-one-step:
  current deployable observation plus previous command and actuator state.

L2-finite-window:
  explicit command-response windows at 0.25s, 0.5s, 1.0s, and 2.0s.

L2-current-tiled-control:
  current frame tiled into the history window to isolate capacity effects.

L3-GRU:
  online recurrent hidden state.

L3-reset/truncated-control:
  same architecture with reset or finite memory to test whether hidden state
  is actually carrying history.
```

Fairness requirements:

- same actor input boundary;
- same actuator-level output `[steer, throttle, brake]`;
- same training budgets and seeds;
- same public evals and no private holdout tuning;
- parameter count, inference cost, and latency reported.

### Step 3: Decisive Task Families

Run the controller matrix on:

```text
T1: reactive emergency avoidance
T2: delayed actuator/response feedback
T3: diagnostic warmup followed by obstacle reveal
T4: same-current, same-recent-window, different-older-history
T5: terminal-boundary near-constraint avoidance
```

Primary metrics:

- success, collision, road departure, spin;
- clearance margin tail, not only mean;
- first-critical action quality;
- short-horizon maneuver gap;
- future braking and yaw authority prediction;
- adaptation latency;
- history-intervention action and margin gaps;
- source diversity and max single-source share.

### Step 4: Self-ID Falsification Tests

Self-ID should be stopped as the main route if at least two of these hold:

```text
1. L2 finite-window matches or beats L3-GRU across decisive tasks.
2. Current-response or one-step feedback matches history models.
3. Wrong/delayed/removed history creates action gaps but not margin gaps.
4. Terminal-boundary positives remain source-singleton after calibrated replay.
5. Reset or zero-current controls explain the effect better than real history.
```

If this happens, the paper route becomes finite-window/current-feedback
actuator-level RL plus rigorous self-ID falsification.

### Step 5: Current-Sim Verdict

Before high-fidelity validation, freeze:

```text
best L1 current-response controller
best L2 finite-window controller
best L3-GRU controller
best actuator-level public base
optional horizon-output shadow head
```

Then write one verdict:

```text
self-ID positive
self-ID negative
self-ID conditional
```

This verdict determines the paper claim level and the high-fidelity validation
target.

## Stage II: High-Fidelity Validation

High-fidelity simulation is a validation layer, not an immediate replacement
for the fast research loop. Use it after the current-sim verdict and controller
set are frozen.

Preferred first backend:

```text
Chrono / Chrono::Vehicle or PyChrono
```

Reason:

- transparent vehicle model;
- modular tire, brake, steering, suspension, and driveline components;
- better fit for reproducible research than closed-source racing games.

Repeat the same actor contract and controller matrix. Add high-fidelity-specific
stressors:

```text
combined slip
load transfer
brake torque dynamics
drive torque dynamics
actuator delay
sensor latency and noise
friction patches
split-friction proxy if supported
throttle plus brake co-activation
```

High-fidelity verdicts:

```text
current-sim positive + high-fidelity positive:
  recurrent self-ID claim survives.

current-sim negative + high-fidelity negative:
  finite-window/current-feedback actuator-level RL is the engineering result.

current-sim positive + high-fidelity negative:
  current-sim self-ID proof was a dynamics artifact.

conditional result:
  publish bounded claim: recurrent history helps only in delayed or ambiguous
  scenarios; finite-window/current-feedback is sufficient elsewhere.
```

## Horizon Output Route

Horizon output should be added as a controller architecture candidate, not as a
shortcut around evidence.

Use receding-horizon semantics:

```text
actor outputs: u_0, u_1, ..., u_{N-1}
runtime executes: u_0 only
next step: re-observe, update history, replan sequence
```

Initial mode:

```text
shadow sequence-delta head
no deployment change
no paper claim unless single-step and sequence-head baselines are compared
```

Move horizon output into the main controller only after the L0/L1/L2/L3
evidence and current-sim verdict are stable.

## Paper Outcomes

### Positive Self-ID Paper

Main claim:

```text
An actuator-level RL evasive driver can use deployable command-response history
to improve terminal-boundary evasive maneuvers under hidden dynamics, and the
effect survives high-fidelity validation.
```

### Negative Self-ID Paper

Main claim:

```text
Under tested active-safety conditions, current-response or finite-window
feedback is sufficient; recurrent self-ID is not automatically induced and not
necessary. The result is still a deployable actuator-level RL driver with
rigorous falsification and high-fidelity validation.
```

### Conditional Self-ID Paper

Main claim:

```text
Finite-window/current-feedback handles most reactive evasive driving, while
recurrent history adds value only when diagnostic evidence is separated from
the emergency reveal or current feedback is delayed and ambiguous.
```

## Execution Rules

- Keep the current harness: manifest-first, review artifact, status update,
  scoreboard update, validation, and commit.
- Do not continue more than one short calibrated replay branch without a
  synthesis decision.
- Do not run PPO or promote a checkpoint from source-singleton history-positive
  rows.
- Do not use private holdout for repair.
- Treat PPO as a proposal generator, not as evidence of self-ID.
- Treat high-fidelity as a validation layer after current-sim evidence is
  frozen.
- Preserve positive and negative results equally.
