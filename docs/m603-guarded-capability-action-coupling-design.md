# M603 Guarded Capability-Action Coupling Design

## Purpose

M603 designs the next no-oracle branch after M602:

```text
belief-level signal exists;
action-level coupling is weak;
therefore design a guarded way to couple capability belief to action.
```

This milestone is design-only:

```text
no code execution
no training
no PPO
no route evaluation
no checkpoint promotion
```

## Diagnosis

The relevant evidence is:

```text
M591: real wrong/delayed hidden histories barely change action.
M598: frozen BC5660 hidden state contains learnable capability signal.
M601: real hidden-history substitutions can change decoded capability belief.
M602: this admits a guarded action-coupling design, not immediate training.
```

So the blocker is not simply hidden observability. The current blocker is:

```text
capability belief is not sufficiently coupled to actuator commands.
```

However, a naive action contrast loss would be wrong. Different hidden
capability predictions do not automatically imply that the action should move
in an arbitrary direction. The action should move only when a row is grounded
by a meaningful control target:

```text
near-boundary margin;
local recovery target;
closed-loop risk residual;
or another simulator-derived training-time target that is not actor input.
```

## Contract

The deployable actor input remains:

```text
P0 human-view no-wheel 72-dim frame + online GRU hidden state
```

No actor input may include:

```text
mu, mass, tire stiffness, brake scale, actuator tau;
slip, tire forces, friction margin;
oracle feasibility labels;
TTC, required clearance, reference path;
success/collision/progress labels;
capability target labels.
```

Capability labels and the M598 head are training/evaluation tools only. They
do not enter the deployable observation.

## Stage 1: Exact No-Update Coupling Evaluator

Before any optimizer step, M604 should implement an exact evaluator that joins
M591-style action movement and M601-style capability movement on the same
matched-current rows.

For each row and variant:

```text
obs = current P0 observation
h_normal = normal recurrent hidden
h_variant = wrong/delayed/shuffled/reset hidden

a_normal = pi(obs, h_normal)
a_variant = pi(obs, h_variant)

c_normal = CapabilityHead(next_hidden(obs, h_normal))
c_variant = CapabilityHead(next_hidden(obs, h_variant))
```

Metrics:

```text
action_distance = ||a_variant - a_normal||_2
capability_z_distance = ||(c_variant - c_normal) / target_std||_2
coupling_gap = capability_z_distance / max(action_distance, eps)
```

Candidate classification:

| Class | Rule | Meaning |
| --- | --- | --- |
| `belief_only_gap` | capability z-distance `>= 0.25`, action distance `< 0.02` | belief moved, action did not |
| `action_and_belief` | capability z-distance `>= 0.25`, action distance `>= 0.02` | existing coupling signal |
| `action_without_belief` | capability z-distance `< 0.25`, action distance `>= 0.02` | likely current-response/context action effect |
| `inactive` | both below threshold | no coupling evidence |

M604 should write:

```text
runs/m604_guarded_capability_action_coupling_evaluator/summary.json
runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv
runs/m604_guarded_capability_action_coupling_evaluator/variant_summary.csv
```

No model weights are changed.

## Stage 2: Grounding Requirement

An action-coupling optimizer is not admitted unless candidate rows are grounded.

Allowed grounding sources:

1. **Local recovery action search**
   Search a small action neighborhood from the current state and hidden branch.
   A target is admitted only if it improves terminal clearance or avoids
   collision relative to the base action while staying in a small trust region.

2. **Terminal-boundary or route-risk residual**
   Use rows close to an active safety boundary where action movement has a
   measurable margin/risk effect.

3. **Source-diverse closed-loop boundary corpus**
   Use source-diverse rows where normal-history behavior is near-boundary and
   a simulator-derived target improves the normal branch without simply making
   all wrong histories safe.

Forbidden grounding:

```text
"capability changed, therefore force action to change"
```

That is ungrounded action separation and remains blocked.

## Stage 3: First Optimizer Scope

The first optimizer, if later admitted, should be narrow:

```text
trainable:
  response_context_fusion
  actor_mean

frozen:
  response_encoder
  context_encoder
  online_gru_cell
  log_std
  capability_head
```

Reason:

```text
M598/M601 already show hidden contains decodable capability. The first repair
should test action coupling without moving the recurrent observer.
```

If this fails, later milestones may consider recurrent hidden fine-tuning, but
not before the action-coupling path has a clean negative result.

## Candidate Loss Terms

Only after Stage 1 and Stage 2 pass, a future optimizer may use:

### Normal Action Anchor

Preserve base behavior on normal histories:

```text
L_normal_anchor = ||pi_new(obs, h_normal) - pi_base(obs, h_normal)||^2
```

### Grounded Target Loss

Only for grounded rows with admitted target actions:

```text
L_grounded_target = ||pi_new(obs, h_normal) - u_target||^2
```

### Variant Guard

Do not make rejected/wrong branches artificially safe unless the row explicitly
requires it:

```text
L_variant_guard = ||pi_new(obs, h_variant) - pi_base(obs, h_variant)||^2
```

This is a guard, not a request to keep wrong-history failure forever. It simply
prevents unplanned branch collapse during the first action-coupling test.

### Trust Region

Constrain parameter drift from the base checkpoint:

```text
L_trust = ||theta_new - theta_base||^2
```

### Exact Gate Order

Acceptance order for any future candidate:

1. no actor input contract violation;
2. exact action-anchor metrics do not regress;
3. M604 coupling-gap candidate metrics move in the intended direction;
4. M591 hidden-action screen does not regress by inventing off-manifold action;
5. M570/M572/M575-style route behavior is not degraded;
6. no PPO or promotion until a later manifest explicitly admits it.

## Pass/Fail For M604

M604 should pass only if:

```text
coupling_rows.csv exists;
variant_summary.csv exists;
belief_only_gap counts are reported for real-history variants;
the evaluator proves it performs no training;
the next branch is decided from candidate counts and grounding availability.
```

If M604 finds many belief-only gaps but no grounded targets, M605 should mine
local recovery or terminal-boundary targets. It should not train.

If M604 finds no source-diverse belief-only gaps, the project should return to
history objective/surface mining or a history-length observability audit.

## Relationship To L3

This design keeps the main target as:

```text
L3: GRU recurrent belief policy
h_t = GRU(h_{t-1}, y_t, u_{t-1})
u_t = pi(y_t, h_t)
```

M603 does not prove L3 superiority. It only designs the next step for coupling
a detected belief signal to action. A later frozen-recipe comparison against
L1 one-step feedback and L2 finite-window history remains necessary.

## Decision

```text
guarded_capability_action_coupling_design_admit_m604_evaluator
```

M603 passes because it pre-registers an exact no-update evaluator, grounding
requirements, allowed trainable scope, forbidden shortcuts, and future gate
order before any actor update.

## Next

```text
M604: implement exact no-update capability-action coupling evaluator.
```
