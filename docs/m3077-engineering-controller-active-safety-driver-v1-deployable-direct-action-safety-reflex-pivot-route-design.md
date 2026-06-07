# M3077 Active Safety Driver v1 Deployable Direct-Action Safety-Reflex Pivot Route Design

## Summary

- status: completed
- decision: `select_m3078_actor_visible_deterministic_direct_action_safety_reflex_materialization_preflight`
- parent audit: `docs/m3076-engineering-controller-active-safety-driver-v1-offtrack-dominant-behavior-direct-action-multi-failure-repair-closed-loop-measurement-result-audit.md`
- next route: `m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight`

M3077 freezes exactly one route after the M3076 pivot: build a deployable,
deterministic, actor-visible safety-reflex policy skeleton that maps the
canonical P0 observation vector to direct `[steer, throttle, brake]`, then
materialize its feature contract, rule table, parameter bounds, actor-input
exclusion guards, measurement admission gates, and claim-boundary rows before
any rollout measurement.

M3077 does not run reset, step, rollout, replay, fitting, PPO, training,
validation, ranking, promotion, current-sim verdict, high-fidelity simulation,
paper evaluation, finite-window-vs-GRU comparison, full-driver completion, or
self-ID testing.

## Pivot Basis

M3076 accepted M3075 as a complete and claim-safe measurement artifact, but the
same-denominator comparison was negative for continuing the offline repair
loop:

```text
M3067 success/collision/offtrack/speed_low: 8 / 4 / 16 / 5
M3075 success/collision/offtrack/speed_low: 6 / 4 / 19 / 4
M3067 success_rate: 0.25
M3075 success_rate: 0.1875
M3067 clearance_margin_mean: 8.495534898357793
M3075 clearance_margin_mean: 8.74188928150522
M3067 raw_action_abs_max: 2.2606801986694336
M3075 raw_action_abs_max: 2.823486328125
M3067 action_clip_fraction_mean: 0.03451952273501378
M3075 action_clip_fraction_mean: 0.03910273341603136
```

The repaired candidate stayed contract-clean and directly deployable, but it
did not improve the primary behavior surface. Collision count stayed unchanged,
success count dropped, offtrack count increased, and raw action pressure
increased. Therefore M3077 closes the default offline target-fitting repair
continuation and starts a deployable safety-reflex branch.

## Selected Route

The selected route is:

```text
actor-visible deterministic direct-action safety-reflex materialization
```

The runtime policy family must satisfy this contract:

```text
input: obs72 only
output: clipped [steer, throttle, brake]
runtime base policy: not required
hidden/oracle/TTC/target/provenance/source/route/outcome/progress/verdict actor inputs: forbidden
```

M3078 must materialize a bounded policy skeleton rather than fit a learned
target tensor. The policy skeleton should be described as deterministic
rule/parameter rows that can later be executed and measured as a full direct
actor. The initial route should use only actor-visible P0 slices:

```text
obs[0:5]: ego velocity, yaw-rate, and acceleration response features
obs[5:12]: actuator state and previous [steer, throttle, brake] commands
obs[12:44]: left/right road-boundary lookahead points
obs[44:72]: visible obstacle slots
```

The intended reflex families are:

```text
collision approach braking and lateral avoidance from visible obstacle slots
offtrack containment from road-boundary corridor pressure
stability damping from yaw-rate, lateral velocity, acceleration, actuator state, and previous command
recovery throttle suppression when brake, offtrack, obstacle, or instability urgency is active
bounded direct-action clipping with no learned base-policy dependency
```

M3078 may define numeric defaults and parameter bounds, but M3077 does not
claim those values are performant. Any future measured claim must pass a later
same-denominator closed-loop measurement and audit.

## Required M3078 Outputs

M3078 must write a materialization artifact set:

```text
actor-visible feature contract rows
deterministic safety-reflex rule rows
direct-action policy config snapshot
actor-input exclusion rows
measurement admission gate rows
claim-boundary rows
gate matrix
summary.json
M3078 document
M3079 result-audit manifest
```

M3078 must fail closed if it cannot prove the materialized candidate preserves
observation shape 72, action shape 3, direct `[steer, throttle, brake]`
semantics, finite values, bounded final actions, no runtime base policy, and no
hidden/oracle actor inputs.

## Measurement Admission

The first future rollout measurement after M3078/M3079 must stay on the
existing same-denominator 32-row current-sim panel unless a separate manifest
pre-registers a different denominator before execution. The measurement must
report, at minimum:

```text
success rows
collision rows
offtrack rows
speed-too-low rows
clearance margin mean and distribution rows
stability rows including sideslip or yaw-pressure proxies
recovery rows
raw action pressure
final action bounds
action clip fraction
actor-contract guards
claim-boundary guards
```

The first measurement cannot claim validation, ranking, promotion, driver
performance, current-sim verdict, high-fidelity readiness, paper evidence,
finite-window-vs-GRU evidence, full-driver completion, repair success, or
self-ID. It can only claim that the selected deterministic safety-reflex
candidate was executed and measured under its pre-registered contract.

## Rejected Routes

M3077 rejects these as the next default:

```text
continue the same offline multi-failure target-fitting repair loop
fit another direct-action target tensor before changing the deployable route boundary
use a residual/base-policy-assisted route as the main deployable actor
promote self-ID, GRU, or paper evidence back to the engineering mainline
start high-fidelity validation before current-sim execution evidence for the new candidate exists
change the actor observation with TTC, target labels, provenance, source labels, route labels, outcome labels, progress labels, verdict labels, or oracle diagnostics
```

Self-ID, GRU, and paper-route evidence remain auxiliary diagnostics. The main
goal is now a deployable active-safety reflex layer judged by collision,
offtrack, clearance, stability, recovery, and robustness evidence.

## Stop Conditions

This branch must synthesize or stop if:

```text
the materialized candidate needs any actor input outside obs72
the candidate cannot directly output [steer, throttle, brake]
the candidate needs a runtime base policy
the first same-denominator measurement regresses primary safety counts without a clear mechanism explanation
the branch starts optimizing one fixed public panel without adding new safety evidence or a pre-registered holdout plan
```

## Next

- follow-up manifest: `experiments/manifests/m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight.json`
- next blocker: `m3078-engineering-controller-active-safety-driver-v1-actor-visible-deterministic-direct-action-safety-reflex-materialization-preflight`
