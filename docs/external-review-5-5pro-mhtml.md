# 5.5pro MHTML External Review

Source: `~/workspace/AutoDrift - 项目评估分析.mhtml`, reviewed at
2026-05-21 21:27 +0800 and updated from the later 2026-05-21 23:50 +0800
snapshot.

This note preserves the important points from the full 5.5pro conversation so
they are not lost behind the local MHTML file. It is a review/decision record,
not a new experiment result.

## Project Assessment

5.5pro's overall assessment:

- AutoDrift is already a reproducible simulation-first RL research platform, not
  just an idea demo.
- The project has a Gymnasium environment, single-track RWD dynamics, PPO
  trainer, recurrent actors, benchmark/evaluation CLIs, scenario corpus mining,
  checkpoint gates, run artifacts, fixed seeds, and milestone documentation.
- The current research problem is no longer "can the project run?" It is
  whether a human-view recurrent driver truly uses action-response history for
  online self-identification under hidden vehicle and road dynamics.

Current best context from the review:

- M2 circular drift reached a strong early result.
- M5 AEB-infeasible obstacle avoidance beat AEB-only, heuristic AES, and
  envelope AES baselines on the then-current benchmark.
- M62 became the margin-retention current best.
- M63/M64/M66 remained negative for proving recurrent response-history
  necessity.
- The next research direction should be counterfactual/intervention evidence,
  not merely more replay of hard seeds.

## Engineering Review

Important engineering recommendations:

- Use source-only exports for sharing. Do not bundle `runs/`, checkpoints,
  PDFs, caches, or `.git` when asking for external review.
- Keep JSON artifacts strict. Non-finite floats should become `null`, and JSON
  writing should use `allow_nan=False`.
- Keep PyTorch probe/test runs under thread limits:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
```

- Avoid eager package imports that require Gymnasium for pure utility imports.
- `train_ppo.py` and `env.py` are getting large; future expansion should split
  actor model, PPO buffer/update, aux objectives, checkpointing, CLI, obstacle
  task, observation builder, and reward builder when a real edit touches those
  areas.
- Checkpoints loaded from CLI paths should be treated as trusted artifacts only.
  Where feasible, move toward safer loading or document the trust boundary.
- Longer-term infrastructure should add CPU-only CI for compile, pytest,
  train-smoke, and eval-smoke.

Current status in this checkout:

- Strict JSON writing is already implemented in `autodrift.artifacts`.
- `Makefile test` already applies the PyTorch thread limits.
- `autodrift.__init__` already lazy-loads `AutoDriftEnv`.
- Source-only packaging remains a release-process concern, not a research
  blocker.
- Large-module refactoring, checkpoint-load hardening, and CI remain future
  infrastructure work.

## Research Framing

The most useful research framing from the review:

```text
Robot learning has shown that action-response history can support rapid online
adaptation under hidden dynamics.

Autonomous emergency avoidance usually keeps explicit planners, reference
trajectories, reachability modules, or dynamics estimators.

The unresolved handling-limit question is whether a human-view recurrent RL
driver can infer maneuver feasibility from its own commands and sensed vehicle
response, without explicit friction parameters or precomputed references.
```

This remains aligned with the user's "professional driver" target:

- no true friction or hidden vehicle parameters as actor input;
- no path/reference planner as the actor's answer source;
- no feasibility label such as AEB/AES/drift-required;
- closed-loop direct control from scene plus vehicle feedback;
- drift-capable but not drift-seeking behavior.

## Solve Versus Verify

The MHTML discussion clarifies an important architecture boundary:

```text
RL solves/proposes the maneuver.
Rules, reachability, CBF, envelope checks, or a safety layer verify/reject it.
```

This means safety verification is not a reason to abandon end-to-end recurrent
RL. The hard part is proposing the maneuver under hidden dynamics:

- Should the car brake?
- Should it do stable AES?
- Should it enter a drift-like maneuver?
- Is the required maneuver feasible under current friction, tire response,
  actuator lag, and brake authority?

Verifier constraints may check a short action sequence and execute only the
first action, MPC-style. The verifier must not feed the actor oracle labels,
friction, reference trajectories, or feasibility decisions.

## Input Sufficiency

The review gives the current 72-value human-view input this interpretation:

- good enough as the current deployable baseline;
- not enough for the final self-identification proof;
- missing important vehicle feedback channels that a skilled driver would feel.

Current useful signals:

```text
vx, vy, yaw_rate, ax, ay
steer_angle, steer_rate
throttle_state, brake_state
previous steer/throttle/brake command
ego-frame road boundary
ego-frame obstacle geometry
```

Known limitations:

- body response alone leaves ambiguity between low friction, weak brakes, wheel
  lock, actuator lag, and tire saturation;
- clean simulator acceleration is too ideal unless later tested with noise,
  bias, delay, and filtering;
- without warm-up/probing, hidden dynamics may not be observable before the
  emergency decision;
- obstacle relative velocity can act as a current-motion proxy, so strict
  self-ID diagnostics should use the zero-relative-velocity context profile.

## Input Additions To Preserve

The MHTML review identifies these deployable additions as important.

Command-response features:

```text
steer_cmd_prev - steer_angle
throttle_cmd_prev - throttle_state
brake_cmd_prev - brake_state
delta_steer_angle
delta_throttle_state
delta_brake_state
delta_vx
delta_vy
delta_yaw_rate
yaw_acceleration
```

Earlier wheel/tire response candidates:

```text
wheel speed
wheel acceleration
front/rear or four-wheel comparison
```

The later input review supersedes the earlier suggestion to feed slip proxies
or ABS/TCS/ESC flags directly into the actor. Those are now diagnostic/logging
or teacher targets, not deployable actor input.

Actuator and force-path feedback:

```text
brake pressure command and actual pressure
drive torque command and actual torque
steering torque or motor current
```

Sensor realism:

```text
IMU noise
IMU bias
sensor delay
low-pass filtering
state-estimation uncertainty
```

Road-surface perception is allowed only as a perception-style cue, not as true
`mu`:

```text
wetness / roughness / surface-class probability
visual road-surface embedding
confidence / uncertainty
```

## Latest Wheel Input Correction

The 23:50 snapshot makes the wheel/tire input rule stricter:

```text
Do not input slip_ratio.
Do not input slip_angle.
Do not input ABS/TCS/ESC flags.
Do not input tire saturation labels.
Do not input true tire force, true normal load, or mu.
```

The reason is both conceptual and numerical. Slip ratio requires a
state-dependent division:

```text
(Romega_i - v_parallel_i) / v_parallel_i
```

That creates low-speed singularities, epsilon/clip choices, sign switching, and
distribution artifacts in lockup, spin, and drift-onset cases.

The cleaner actor-facing signals are the raw components:

```text
Romega_i
v_parallel_i
optional v_perp_i
optional fixed-scale error: (Romega_i - v_parallel_i) / fixed_v_scale
```

`v_parallel_i` must be each tire contact patch's local ground speed along the
wheel rolling direction. It must not be the vehicle-center speed and must not be
computed from the average of wheel speeds, because wheel speed is the signal
used to detect lockup and spin.

The revised minimum observable actor set is:

```text
commands
actual actuator states
wheel circumferential speeds
local wheel-ground speeds
IMU ax / ay / yaw_rate
road and obstacle geometry
```

For current single-track AutoDrift, this becomes a temporary front/rear
approximation:

```text
Romega_front
Romega_rear
v_parallel_front
v_parallel_rear
```

This correction is implemented and tested in M92:

```text
docs/m92-local-wheel-ground-speed-input-plan.md
docs/m92-local-wheel-ground-speed-observability-audit.md
```

## Latest Minimum-Input Principle

The later input discussion also sharpens the general rule for actor inputs:

```text
actor inputs should be sensor-direct or minimally calibrated/fused;
diagnostic ratios, controller mode flags, oracle labels, and planner answers
belong only in logging, probes, teachers, verifiers, or baselines.
```

The minimum closed-loop observability chain is:

```text
known control commands
-> actual actuator feedback
-> wheel/tire raw response when available
-> body inertial response
-> road and obstacle geometry
```

The important distinction is command-response pairing. Without the command, a
weak response cannot distinguish "I did not ask for control" from "I asked and
the vehicle could not deliver it." Without actual actuator state, weak response
cannot distinguish actuator lag from tire/road limits.

Current no-wheel AutoDrift remains the primary driver input because M91/M92 did
not admit the current single-track wheel profiles. The future four-wheel profile
should be tested as a new sensor branch, not silently folded into the baseline.

## Latest Experiment Ladder

The saved MHTML recommends the input research order now preserved in
`docs/m91-input-observability-audit-protocol.md`:

```text
A. supervised information-observability probes;
B. minimum-set sensor ablations;
C. frozen-recipe RL profile comparison;
D. matched hidden-dynamics wrong-history counterfactuals;
E. optional-sensor admission gates.
```

The reliability rule is to avoid tuning PPO separately for each input profile.
Use probes first, find one stable training recipe, freeze the recipe, and then
train compared profiles with the same seeds, budget, reward, curriculum,
evaluation corpus, auxiliary losses, and gates. Only after this comparison
should the best primary profile be iterated further.

## Wheel Response Decision

The strongest new decision is that wheel/tire response should become the next
major input branch after the current M80 sanity check.

The reason is not raw performance. The reason is evidence: if the driver is
supposed to behave like a skilled operator, it needs a machine version of tire
feedback.

Persisted execution roadmap:

- `docs/m81-wheel-response-input-roadmap.md`
- `docs/observation-contract.md`
- `docs/implementation-plan.md`
- `docs/m67-self-id-decision-ledger.md`

Current status after M91/M92: the idea remains valid, but the current
single-track front/rear wheel profiles are not admitted into the primary driver
input. M91-I rejected the raw front/rear proxy, and M92 rejected the
single-track local-ground-speed variants as primary PPO inputs. A real
four-wheel model or a better matched corpus is needed before wheel sensing can
return to the main driver profile.

## Warm-Up And Probing

The review reinforces that self-identification requires excitation:

```text
no warm-up: obstacle appears immediately
short warm-up: about 0.3 s
medium warm-up: about 1.0 s
long warm-up: about 2.0 s
```

If self-ID only appears after warm-up, that is acceptable and realistic. A
skilled driver is also continuously sensing the vehicle before the emergency.

Active probing should be safety-bounded:

- mild steering pulse;
- small brake tap;
- small throttle/brake modulation;
- no reward for dangerous probing that sacrifices margin.

## Required Proof Standard

Aggregate success is not enough. A strong self-ID claim needs counterfactual
evidence:

```text
normal history performs better than reset/zero/wrong history
wrong matched history induces wrong action or lower clearance
wheel-history intervention changes behavior when current geometry is matched
latent predicts future handling envelope better than memoryless baseline
margin retention does not regress versus M62-class baseline
```

Important ablations:

```text
reset hidden
zero current response
zero all explicit response
zero action history
zero wheel input
delayed history
action-response mismatch
wrong history from matched hidden dynamics
high-mu wheel history injected into low-mu episode
low-mu wheel history injected into high-mu episode
```

Useful latent/probe targets:

```text
future max braking decel
future max lateral acceleration
yaw authority
steering delay estimate
brake authority estimate
understeer / oversteer tendency
stable AES feasibility
drift AES feasibility
drift recoverability
```

## Queue Decision

Historical queue decision from the first MHTML review:

```text
M80: outcome objective-only sanity check.
M81: wheel/tire response input branch and wheel-specific self-ID gates.
```

Do not use M80 as the final answer to the project. It is only a blocker check
for the current outcome-intervention objective. M81 addresses the deeper input
gap identified by the full MHTML review.

Current status after the later work:

- M91/M92 executed the input-observability audit path and rejected the current
  single-track wheel profiles as primary PPO inputs.
- M93-M98 found and optimized a no-wheel hidden-envelope belief objective.
- M99/M100 showed that hidden belief alone was not enough; the actor still did
  not depend on recurrent history.
- M101 produced the first behavior-level reset/zero-response dependence signal,
  but hidden-envelope retention regressed on braking/lateral probe targets.
- M102 recovered hidden-envelope retention under softer actor coupling, but the
  reset/zero-response behavior-dependence signal disappeared again.

The current next research step is therefore not another wheel-profile PPO run.
It is M103 outcome-aware actor coupling: mine or construct snippets where
normal carried history actually improves clearance or success over reset,
zero-response, delayed-history, or wrong-history interventions, then apply
actor-coupling pressure only on those outcome-relevant snippets.

The stricter input-contract takeaway is now also preserved as
`docs/m104-minimum-observable-input-contract.md`.
