# M67 Self-ID Decision Ledger

This ledger records the M67 self-identification advice and where each decision
is persisted. It is the short recovery file to read before continuing M67 work.

## Current Answer

Yes, the two 5.5pro review threads are now persisted:

- belief/self-identification roadmap:
  `docs/m67-belief-self-identification-roadmap.md`;
- observation/input profile audit:
  `docs/m67c-input-profile-audit.md`;
- strict observation profile implementation and result:
  `docs/m67d-strict-self-id-observation-profile.md`;
- queue/status pointer:
  `experiments/research_queue.csv` and `experiments/research_status.json`.

This file adds a compact index so the project does not depend on remembering
which M67 document contains which decision.

## Adopted Belief-Learning Direction

Do not make the next main line "more replay" or "larger response-prediction
loss". M66 already showed that response-necessity replay alone does not make
the recurrent hidden state behavior-critical.

Adopted framing:

```text
z_t = q_phi(command-response history)
a_t = pi_theta(scene_t, ego_t, z_t)
```

The latent should represent an action-relevant dynamics envelope, not just a
single physical parameter:

```text
braking authority
lateral / yaw authority
steering and brake delay
understeer / oversteer tendency
stable-AES feasibility
drift-AES feasibility
drift recoverability
```

Persisted in:

- `docs/m67-belief-self-identification-roadmap.md`

## Privileged Upper Bound

Decision: before training another deployable student, prove whether hidden
dynamics can improve the current hard corpus at all.

Completed:

- M67-A privileged upper-bound harness;
- M67-B from-scratch privileged teacher training;
- result: from-scratch teacher did not beat `m62_a250` on M65
  response-critical seeds.

Current interpretation:

```text
The upper-bound idea is still valid, but the teacher must preserve M62 driving
behavior first. A weak from-scratch teacher is not a useful oracle.
```

Completed follow-up:

- `m67e-warm-started-privileged-teacher`;
- result: the M62-compatible privileged teacher infrastructure works, but the
  best checkpoint only improves M65 mean margin by `0.000804` with no success
  gain, so it is not a credible upper-bound breakthrough.

Persisted in:

- `docs/m67a-privileged-upper-bound-harness.md`
- `docs/m67b-full-privileged-upper-bound-training.md`
- `docs/m67-belief-self-identification-roadmap.md`
- `experiments/research_queue.csv`

Note: the first roadmap used the label "M67-C" for the warm-started teacher.
After the input-profile audit was inserted, the current queue label is
`m67e-warm-started-privileged-teacher`.

## Observation Profile Decisions

Current 72-value human-view input remains the main deployable baseline:

```text
0-8    ego response
9-11   previous physical commands
12-43  road boundary points in ego frame
44-71  obstacle slots
```

Accepted score from the review:

```text
deployable / human-view input: 7.5 / 10
self-ID proof input:          6.0 / 10
```

Reason: it is deployable and useful, but not clean enough to make
reset/zero-response evidence decisive.

Persisted in:

- `docs/m67c-input-profile-audit.md`
- `docs/observation-contract.md`

## Strict Context Profile

Accepted issue:

```text
obstacle rel_vx / rel_vy are context-side ego-motion proxies
```

For static obstacles, obstacle relative velocity can re-expose ego velocity and
yaw rate even when response channels are zeroed. That weakens zero-response
diagnostics.

Implemented decision:

```text
obstacle_relative_velocity_mode = "ego"   # default historical behavior
obstacle_relative_velocity_mode = "zero"  # strict self-ID diagnostic profile
```

M67-D result:

```text
strict context preserves M62 baseline success
but does not make reset/zero-response ablations behavior-critical
```

Interpretation:

```text
The cleanup is necessary, but not sufficient. The next proof gate needs
wrong-history / matched-history interventions, not only reset or zero-response.
```

Persisted in:

- `src/autodrift/env.py`
- `configs/ppo_m67d_strict_self_id_context_driver.json`
- `docs/m67d-strict-self-id-observation-profile.md`

## Deferred Input Work

These are accepted but intentionally deferred until matched action-divergent
pairs and wrong-history diagnostics are clearer.

Enhanced OSI response profile:

```text
yaw_acceleration
command actuator errors
delta_vx / delta_vy / delta_yaw_rate
command deltas
```

Noisy IMU / sensor robustness:

```text
noise, delay, and bias on ax, ay, yaw_rate, steer / actuator state
```

Reward cleanup:

```text
reduce hidden speed_ref / beta_target shaping for emergency self-ID claims
emphasize collision, clearance margin, boundary, spin, smoothness, progress,
and recoverability
```

Persisted in:

- `docs/m67c-input-profile-audit.md`

## Forbidden Deployable Actor Inputs

These must stay out of deployable actors:

```text
mu
mass_scale
tire_stiffness_scale
brake_scale
drive_scale
actuator_tau
obstacle_label
AEB feasible / AES feasible / drift_required
required lateral clearance
oracle stopping distance
path lateral error
path heading error
beta_target
friction-step flag
TTC
```

They may be used for teacher-only observations, diagnostics, logging, corpus
mining, or training-time losses, but not as student actor input.

Persisted in:

- `docs/m67c-input-profile-audit.md`
- `docs/m67-belief-self-identification-roadmap.md`
- `docs/observation-contract.md`

## Required Future Gates

The next self-ID proof should rely on causally meaningful interventions:

```text
matched hidden-dynamics pairs
wrong history from the matched vehicle
action-response mismatch
delayed history
zero action history
reset hidden
zero current/all response
```

Pass evidence should include:

```text
normal history margin > wrong-history margin
wrong history induces wrong action on matched action-divergent cases
latent predicts future response envelope better than memoryless baseline
strict margin retention does not regress versus M62-class baseline
```

Persisted in:

- `docs/m67-belief-self-identification-roadmap.md`
- `docs/m67d-strict-self-id-observation-profile.md`

## Next Action

Continue with:

```text
m73-active-probing-warmup-harness
```

Implementation intent:

```text
use small safety-bounded control excitation before obstacle reveal
compare normal probing history with wrong matched probing history
require wrong/reset/zero probing history to reduce outcome under strict visible matching
```

M70 showed that M69 wrong-history candidates do not degrade success or margin.
M71 added the outcome-sensitive miner but still found zero accepted passive
matched-snapshot cases. M72 added passive warm-up reveal, but it also found zero
accepted outcome-sensitive cases. Do not proceed directly to student OSI
distillation yet.
