# Paper-Route Plan: Finite-Window vs GRU Evasive Driver Evidence

## Purpose

This plan reframes the next phase of AutoDrift / General Evasive Driver as a
paper-oriented evidence program rather than another narrow proof-row repair
loop. The project should no longer assume that an online GRU is inherently the
right final controller. A finite-window command-response controller may be
strong enough for engineering use, and the GRU claim should only be made where
experiments show incremental value beyond practical finite windows.

The paper route should answer:

```text
When is current-response feedback enough?
When is finite-window history enough?
When does recurrent belief add measurable value?
Which historical gates and repair mechanisms are still necessary?
```

## Non-Negotiable Actor Contract

All controller variants must obey the same deployable input boundary.

Allowed deployable inputs:

- ego kinematics and IMU-like response;
- steering, throttle, and brake actuator state;
- previous physical commands;
- road, free-space, and obstacle geometry in ego frame;
- history represented either explicitly as a finite window or implicitly as a
  recurrent state.

Forbidden deployable inputs:

- `mu`, mass, CG, tire stiffness, brake scale, or actuator time constants;
- slip ratio, slip angle, tire force, tire saturation, or friction margin;
- AEB/AES/drift-required feasibility labels;
- controller mode, reference trajectory, TTC, required clearance, oracle
  stopping distance, path error, heading error, path curvature;
- collision, success, progress, or any precomputed answer.

Training-time teachers, diagnostics, miners, and paper analysis may use hidden
state or oracle quantities, but those values must not enter the deployed actor
input.

## Claim Ladder

The paper should use the weakest claim supported by evidence.

### Claim A: Deployable Feedback Driver

The controller uses deployable ego response, actuator state, previous commands,
and scene geometry to perform emergency evasive driving under randomized hidden
dynamics.

This is the engineering baseline claim. It does not require proving GRU
self-identification.

### Claim B: History-Conditioned Output Feedback

Multi-step command-response history improves future capability prediction,
first-critical action quality, or terminal-boundary margin relative to
current-only and one-step feedback baselines.

This claim can be supported by either finite-window or GRU controllers.

### Claim C: Recurrent Belief Advantage

An online GRU or recurrent belief state outperforms practical finite-window
controllers on tasks where diagnostic information occurs outside the finite
window, where the delay between diagnosis and obstacle reveal varies, or where
weak evidence must be integrated over time.

This claim should be limited to scenarios where L3 recurrent models beat
matched L2 finite-window baselines under fair capacity and training controls.

### Claim D: Strong Self-Identification

Wrong, delayed, reset, or mismatched history interventions degrade
first-critical action, short-horizon maneuver quality, or terminal-boundary
outcome while the normal-history policy remains successful.

This is a mechanism claim. It should be used only for source-diverse,
non-duplicate scenarios, not for single protected rows or stale lineage
artifacts.

## Baseline Model Matrix

All comparisons must use the same action contract:

```text
u_t = [steer_command, throttle_command, brake_command]
```

The primary comparison matrix is:

```text
L0-current:
  current deployable frame only; no recurrent state; no explicit history stack.

L1-one-step:
  current deployable frame plus previous physical command and actuator state.
  This represents a strong augmented current-response controller.

L2-finite-window:
  explicit command-response windows at 0.25s, 0.5s, 1.0s, and 2.0s.
  This is the main engineering challenger to GRU.

L3-GRU:
  current deployable frame plus online GRU hidden state.

L3-reset-control:
  same architecture as L3 but with hidden reset or periodic truncation.
  This tests whether the GRU is acting as memory or only as a larger network.
```

Fairness requirements:

- same action space and actuator-level output;
- same train/eval splits;
- same reward and terminal metrics when training;
- no hidden or oracle inputs in any actor;
- report parameter counts and inference cost;
- use identical public gates, fresh evals, and paper holdout protocol.

## Task Families

### Family 1: Reactive Evasive Driving

Goal: measure the engineering baseline.

These are ordinary evasive-driving scenarios where current response and recent
feedback are expected to be strong. The likely result is:

```text
L1 or L2 approximately equals L3.
```

That is not a failure. It means the engineering controller does not need a
strong recurrent-belief claim for these cases.

Metrics:

- success rate;
- collision rate;
- road departure rate;
- spin rate;
- clearance margin mean and tail;
- control smoothness;
- recovery after maneuver.

### Family 2: Same-Current, Different-Older-History

Goal: isolate whether longer history contains information unavailable to
current feedback and recent finite windows.

Construct matched pairs satisfying:

```text
current observation is matched;
previous command and actuator state are matched;
recent K-step command-response window is matched;
older command-response history differs;
future capability differs.
```

Test K values:

```text
0.25s, 0.5s, 1.0s
```

The key test is whether L3 can use older diagnostic evidence when L2 with the
same K cannot.

Metrics:

- future braking envelope prediction error;
- future yaw authority prediction error;
- first-critical action distance to teacher or local target;
- terminal-boundary clearance margin;
- wrong-history degradation under source-diverse interventions.

### Family 3: Active Diagnostic Warmup

Goal: ensure history has usable information.

Warmup modes should use deployable, low-amplitude actions:

```text
brake_tap
steer_pulse
brake_plus_steer
throttle_plus_brake
lift_off_plus_steer
micro_countersteer
natural_policy
```

Episode structure:

```text
Phase 1: diagnostic warmup
Phase 2: current/recent-window alignment
Phase 3: obstacle reveal and first-critical action window
Phase 4: recovery and terminal-boundary outcome
```

The paper should report whether diagnostic warmup improves the value of
history, and whether that value is captured by finite windows or requires GRU.

### Family 4: Variable Diagnostic Delay

Goal: test the finite-window tradeoff.

Delay from diagnostic cue to obstacle reveal:

```text
0.2s, 0.5s, 1.0s, 2.0s, 3.0s
```

Expected interpretations:

- if short L2 windows fail and long L2 windows match L3, the result supports a
  history-conditioned controller but not necessarily GRU;
- if all practical L2 windows fail while L3 remains strong, the result supports
  recurrent-belief advantage;
- if L1 already matches L3, current-response feedback is sufficient for this
  task.

### Family 5: Source-Rich Extreme Dynamics

Goal: replace stale proof rows with source-rich scenarios.

Current-model faults:

- global friction drop;
- front lateral authority drop;
- rear lateral authority drop;
- brake authority drop;
- steering fault;
- mass and CG shift.

Proxy faults:

- drive authority drop;
- delay/noise fault;
- combined fault.

Future-only faults until simulator support exists:

- single-wheel grip collapse;
- tire puncture or blowout;
- split-mu left/right;
- stuck caliper or single-wheel brake pull;
- true asymmetric half-shaft torque loss;
- wheel-speed sensor dropout or bias;
- steering pull from asymmetric front damage.

This family should preserve source geometry, target geometry, fault family,
fidelity class, onset bucket, severity, warmup mode, current-frame match
metrics, action divergence, and terminal-margin sensitivity.

## Evidence Program

### Stage 1: Gate Utility and Research Debt Audit

Before adding more training machinery, audit the existing gates and historical
repair tools.

Inputs:

- good candidates that were promoted or admitted;
- known bad candidates that caused proof washout or behavior regression;
- near-miss candidates just outside a safe interpolation boundary;
- no-op or tiny random perturbation candidates.

Run gate stacks:

```text
Stack A: minimal engineering
  contract + behavior + fresh/OOD + success/collision/clearance

Stack B: balanced public
  Stack A + one compact source-diverse proof gate + one active rollback pair

Stack C: full historical
  all old public surfaces, row15/row16, family-intersection, source-diverse,
  protected rows, and exact historical objectives
```

Output:

```text
docs/gate-utility-matrix.md
```

For each gate:

- known bad caught count;
- good candidate false reject count;
- unique information relative to other gates;
- runtime cost;
- lineage specificity;
- recommendation: core, research-only, extended-regression, legacy, or
  deprecated.

### Stage 2: Capability Prediction Before Policy Training

Do not immediately run PPO. First test whether the information is present.

Targets:

- future braking deceleration envelope;
- future yaw authority;
- future lateral acceleration response;
- actuator response lag proxy;
- recovery margin after maneuver;
- first-critical action quality.

Compare L0/L1/L2/L3 on the same tasks. If L2 and L3 cannot predict future
capability better than L1, the scenario does not yet require history.

### Stage 3: Controlled Behavior Comparison

Train or evaluate L0/L1/L2/L3 under matched conditions.

Report:

- in-distribution performance;
- source-rich extreme dynamics performance;
- current-ambiguous performance;
- variable-delay performance;
- finite-window length curve;
- GRU reset/truncation ablation;
- inference cost and model size.

### Stage 4: Mechanism Intervention

Only after Stage 2 and Stage 3 show history value, run intervention tests.

Interventions:

- reset hidden;
- zero explicit response history;
- delayed history;
- stale history;
- wrong matched history from a different hidden dynamics family;
- command-response mismatch;
- finite-window truncation.

Evidence levels:

```text
Level 1: current-response adaptation
Level 2: history changes capability prediction or latent belief
Level 3: history changes first-critical action or short-horizon maneuver
Level 4: history changes terminal-boundary outcome
```

Level 4 is valuable but should not be required for every experiment.

### Stage 5: Guarded RL Only After Evidence Is Stable

Guarded PPO or longer RL continuation should be admitted only after:

- actor contract passes;
- L0/L1/L2/L3 comparison has identified the target controller family;
- source-rich or current-ambiguous data exists;
- gate utility audit has removed stale hard blockers from the active path;
- public proof and engineering gates are separated;
- paper holdout policy is defined.

PPO should be treated as a proposal generator, not as the primary source of
mechanism evidence.

## Route Decision Rules

### If L1 Matches L2 and L3

Decision:

```text
Engineering route: current-response feedback controller.
Paper claim: deployable closed-loop feedback is strong; no strong history claim.
GRU route: research-only.
```

Do not continue adding self-ID proof machinery to the main training path.

### If L2 Matches L3

Decision:

```text
Engineering route: finite-window history-conditioned controller.
Paper claim: multi-step command-response history helps, but GRU is one compact
implementation rather than a necessary mechanism.
```

Keep GRU as a compact recurrent implementation, but do not claim universal GRU
advantage.

### If L3 Wins Only in Delayed or Variable-Memory Tasks

Decision:

```text
Engineering route: choose L2 or L3 by latency, robustness, and simplicity.
Paper claim: recurrent belief has conditional advantage in delayed,
current-ambiguous, or variable-memory self-identification scenarios.
```

This is a strong and realistic paper route.

### If L3 Wins Broadly

Decision:

```text
Engineering route: recurrent driver remains primary.
Paper claim: recurrent belief improves handling-limit evasive driving under
hidden dynamics when compared to practical finite-window controllers.
```

This is the only route that supports a broad GRU recurrent-belief claim.

### If No History Model Beats Current Feedback

Decision:

```text
Task design is insufficient for self-ID evidence.
Stop PPO and proof-row repair.
Return to scenario design, diagnostic warmup, and source-rich data generation.
```

## Paper Outline

### Main Story

The paper should not claim that GRU is always necessary. It should claim that
deployable command-response feedback can produce robust evasive driving, then
identify when finite-window history or recurrent belief adds value.

### Suggested Sections

1. Introduction: emergency evasive driving under hidden vehicle and surface
   dynamics.
2. Problem formulation: deployable output-feedback control without oracle
   inputs.
3. Controller families: current feedback, finite-window feedback, recurrent
   belief.
4. Scenario families: reactive, current-ambiguous, diagnostic warmup,
   variable-delay, source-rich extreme dynamics.
5. Training and evaluation harness: proof gates, generalization gates, and
   promotion discipline.
6. Experiments: L0/L1/L2/L3 comparison, history-length curve, intervention
   tests, and source-rich evaluation.
7. Ablations: gate utility, hidden reset, finite-window truncation, diagnostic
   removal, and history mismatch.
8. Discussion: when finite-window is enough, when GRU helps, and what remains
   before high-fidelity or real-vehicle validation.

### Required Tables

- actor input contract table;
- scenario family table;
- L0/L1/L2/L3 model table with parameter counts and inference cost;
- main performance table;
- history-length curve table;
- intervention/gate table;
- gate utility matrix;
- failure taxonomy table.

### Required Figures

- output-feedback control diagram;
- diagnostic warmup and obstacle reveal timeline;
- finite-window vs GRU history diagram;
- performance vs diagnostic-delay curve;
- margin distribution plots;
- intervention effect plots;
- gate stack decision matrix.

## Repository Plan

Immediate docs and harness updates:

1. Add this plan as the governing paper-route document.
2. Record a process milestone that says M1182 no-residual adapter remains useful
   infrastructure but no longer determines the main scientific route by itself.
3. Add a follow-up gate-utility audit milestone before any broad training or
   promotion attempt.
4. Add a follow-up L0/L1/L2/L3 experiment design milestone before making a
   GRU-first paper claim.

Recommended next milestones:

```text
M1182:
  no-residual source-rich adapter implementation.
  Scope: infrastructure only, useful for source-rich data generation.

M1183:
  paper-route gate utility audit design.
  Scope: classify old gates as core, research-only, extended regression,
  legacy, or deprecated.

M1184:
  historical candidate gate utility matrix.
  Scope: run gate stacks A/B/C over historical good/bad/near-miss candidates.

M1185:
  L0/L1/L2/L3 baseline design.
  Scope: define fair controller families, observation windows, parameter
  budgets, and train/eval splits.

M1186:
  current-ambiguous and diagnostic-warmup dataset design.
  Scope: same-current, same-recent-window, different-older-history scenarios.

M1187:
  capability prediction probe.
  Scope: future envelope prediction before policy training.

M1188:
  controlled behavior comparison.
  Scope: compare L0/L1/L2/L3 on reactive and current-ambiguous tasks.

M1189:
  route synthesis.
  Scope: decide engineering route, paper claim level, and which gates stay
  active.
```

## What This Changes

This plan changes the project from:

```text
keep repairing historical wrong-history proof rows until PPO can continue
```

to:

```text
build paper-quality evidence that separates current feedback, finite-window
history, and recurrent belief; keep only the gates that protect real failures.
```

The current public-gate base remains valuable, but it should be treated as a
proof-hardened lineage point, not as evidence that the final paper route must
be GRU-only or row-specific.
