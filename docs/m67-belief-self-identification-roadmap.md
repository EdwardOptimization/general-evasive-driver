# M67 Belief Self-Identification Roadmap

This note records the external 5.5pro review recommendation and the project
decision after M66/M67-A/M67-B. It is a roadmap, not a promotion claim.

## Decision

Adopt the core recommendation:

```text
Do not make the next main line "more replay" or "larger response-prediction
loss". Treat the driver as a POMDP belief-learning problem.
```

The deployable policy should learn a latent belief from its own recent commands
and sensed response:

```text
z_t = q_phi(response_history_0:t, action_history_0:t-1)
a_t = pi_theta(scene_t, ego_t, z_t)
```

The latent does not need to predict a single physical parameter such as `mu`.
The useful target is the current dynamics envelope:

```text
braking authority
lateral/yaw authority
steering and drive/brake delay
understeer or oversteer tendency
stable-AES feasibility
drift-AES feasibility
drift recoverability
```

Actor inputs stay clean. Hidden parameters, obstacle labels, controller modes,
oracle feasibility labels, and route/path errors remain forbidden deployable
actor inputs. Privileged values may be used only by teachers, diagnostics,
training-time losses, and gates.

## Why The Direction Changed

M62 remains the current best margin-retention candidate, but M63/M64 did not
prove recurrent self-identification. Resetting hidden state, zeroing current or
all response features, and zeroing action history did not reliably weaken
success or clearance margin.

M66 then tested whether response-necessity seed replay plus a stronger
response-prediction auxiliary would make response history behavior-critical. It
did not. No full M66 checkpoint passed strict margin retention, and the closest
checkpoint did not improve the paired self-identification signal.

Therefore, the next research question is not "can we replay harder seeds?" It
is:

```text
Does hidden dynamics information change the right action and improve outcomes on
the critical corpus?
```

If the answer is no, the corpus is not a good self-identification corpus. If the
answer is yes, a deployable recurrent student can be trained to approximate the
teacher's hidden-dynamics judgment from action-response history.

## Adopted Milestone Sequence

### M67-A: Oracle Upper-Bound Harness

Build a privileged teacher/evaluation path before training another student. The
teacher sees hidden dynamics only through a teacher-only observation mode, while
the deployable baseline remains human-view.

Status: complete as infrastructure.

Artifacts:

- `configs/ppo_m67a_privileged_upper_bound_teacher.json`
- `src/autodrift/privileged_upper_bound.py`
- `docs/m67a-privileged-upper-bound-harness.md`

### M67-B: Full Privileged Teacher Attempt

Train a full privileged teacher from scratch and compare it against `m62_a250`
on the M65 response-critical corpus.

Status: complete as a negative upper-bound attempt.

Result:

- `m62_a250`: success `0.615385`, mean margin `0.304161`;
- best swept from-scratch privileged teacher `m67a_232`: success `0.500000`,
  mean margin `0.213538`;
- conclusion: the from-scratch teacher never reaches M62's retained driving
  behavior, so it is not a credible oracle upper bound.

Artifact:

- `docs/m67b-full-privileged-upper-bound-training.md`

### M67-C: Warm-Started Privileged Teacher

Completed later under queue label `m67e-warm-started-privileged-teacher`. Build
a privileged teacher that preserves M62's human-view driving behavior and
appends hidden dynamics as teacher-only context.

Goal:

```text
baseline behavior = M62-class human-view driving
extra information = full hidden dynamics packet
test = whether hidden dynamics improves M65 margin/action choices
```

Preferred design:

- keep the first 72 deployable inputs in the same semantic order;
- reuse or partially initialize M62's response/context encoders when possible;
- append the 10-value full hidden packet as a separate privileged context branch;
- use a conservative anchor to avoid washing out M62 behavior;
- evaluate every dense checkpoint against M65 and strict margin-retention gates.

Pass condition:

- teacher success or mean clearance margin improves over `m62_a250` on
  response-critical seeds;
- improvement is not only aggregate reward;
- per-seed deltas show action-relevant hidden-dynamics advantage.

Status: complete as a weak/negative upper-bound result. The implementation
worked and the best swept checkpoint `m67e_004` preserved M62 success, but it
only improved M65 mean margin by `0.000804` with an even 13/13
improved/regressed seed split. This is not a meaningful hidden-dynamics
upper-bound gap.

Conclusion: do not train a student yet. Re-mine the corpus.

### M67-D: Matched Action-Divergent Corpus

Mine or construct cases where current visible state and scene are similar but
hidden dynamics require different actions.

Desired sample:

```text
same or near-same road geometry
same or near-same obstacle geometry
same or near-same ego state
different hidden dynamics
teacher or oracle action differs
wrong-history or wrong-hidden action reduces margin or causes collision
```

Useful score terms:

- teacher action distance between hidden conditions;
- terminal margin gap under wrong hidden/history;
- normal versus reset-hidden margin gap;
- normal versus shuffled-history margin gap;
- low-friction, weak-brake, or slow-actuator ambiguity.

This corpus is more valuable than ordinary hard seeds because it directly tests
"looks the same, drives differently".

Status: initial harness complete later under queue label
`m68-matched-action-divergent-corpus`. The M65 smoke found 10/26 strict visible
matches and 6 paired-action divergent pairs, but 0 privileged-packet divergent
pairs. Broader mining is still required before student training.

### M67-E: Teacher-Student OSI Pretraining

Train a deployable recurrent student to infer action-relevant dynamics from
history, not from hidden parameters.

Candidate losses:

```text
PPO loss
+ weighted teacher action distillation
+ future response prediction
+ dynamics-envelope prediction
+ risk or terminal-margin value prediction
```

Distillation weights should be high only where hidden dynamics changes the
correct action or terminal margin. Do not average teacher imitation across easy
states where all dynamics require the same action.

The teacher can use hidden parameters during training. The student actor cannot.

### M67-F: Outcome-Bound Counterfactual Intervention

Do not train "different for the sake of being different". Intervention losses
should fire only when the intervention changes outcome quality.

Preferred pairwise form:

```text
normal history rollout -> margin m_plus
reset/zero/wrong-history rollout -> margin m_minus
if m_plus > m_minus + delta:
    increase probability/value of normal-history behavior
    do not force wrong-history behavior to match it
```

Interventions to support:

- reset recurrent state;
- zero current response;
- zero all response history;
- zero action history;
- shuffled history;
- delayed history;
- action-response mismatch;
- wrong history from paired hidden dynamics.

The strongest intervention should be wrong history from a matched hidden-dynamics
pair, because it tests whether the policy's internal belief is causally tied to
the correct vehicle.

### M67-G: Pre-Emergency Warm-Up And Active Probing

A real driver is not identifying the car only at the moment the obstacle
appears. Future tasks should include a warm-up phase before the emergency:

```text
0.5 s to 2.0 s normal driving or mild maneuver
hidden dynamics already randomized
obstacle appears later
GRU hidden persists into emergency phase
```

Curriculum:

- long warm-up, obstacle late;
- medium warm-up;
- short warm-up;
- hidden dynamics change mid-episode;
- noise, latency, and out-of-range dynamics.

Active probing is allowed only if it remains safety-compatible. Small steering,
brake, or throttle modulations may help identification, but unsafe probing must
be penalized.

## Final Evidence Standard

The final claim should not be:

```text
RL success rate is high.
```

The target claim is:

```text
The human-view recurrent driver succeeds at emergency avoidance and its behavior
causally depends on its own action-response history.
```

Required evidence:

- strict margin retention versus M62-class baseline;
- paired hidden-dynamics success and margin do not regress;
- reset, zero-response, no-action-history, and wrong-history variants are
  measurably weaker on response-critical seeds;
- latent probes predict future response envelope better than memoryless probes;
- wrong history induces wrong action or lower margin in matched
  action-divergent cases;
- warm-up response helps the policy choose earlier or safer emergency maneuvers.

Only after these pass should a checkpoint be described as an ideal driver
candidate.
