# M2475 High-Fidelity Interface External Backend Route Design

- status: completed
- decision: `external_backend_route_to_dependency_api_audit`
- manifest: `experiments/manifests/m2475-high-fidelity-interface-external-backend-route-design.json`
- parent adapter smoke: `docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md`
- parent summary: `runs/m2474_high_fidelity_interface_current_sim_adapter_smoke/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- next milestone: `m2476-high-fidelity-interface-external-backend-dependency-api-audit`
- external high-fidelity simulation installed/imported/executed in M2475: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2475: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2475 selects the next bounded external-backend route after HF0 contract
implementation and current-sim adapter smoke. It does not choose a validation
result, install a simulator, import external high-fidelity packages, or run
simulation.

The useful boundary from M2472-M2474 is now:

```text
DynamicsBackend reset/step/close
ActorView as the only P0 extractor input
P0 observation shape: 72
actor action shape: 3
diagnostics separated from actor input
```

The next step should audit whether an external backend can satisfy that
boundary before implementation.

## Route Decision

Decision:

```text
external_backend_route_to_dependency_api_audit
```

Primary candidate direction:

```text
open auditable high-fidelity vehicle dynamics layer
preferred family: Chrono / Chrono::Vehicle route
```

This follows the post-M2470 route plan preference for an open, auditable
high-fidelity vehicle dynamics layer. M2475 does not claim that Chrono is
installed, importable, API-compatible, or selected for validation. It only
selects the next audit route.

Fallback direction:

```text
source-only FourWheelDriftModel adapter preflight
```

The fallback is admissible if the external dependency/API audit finds that
external simulator installation, licensing, build requirements, bindings, or
state extraction are not locally auditable without nonlocal decisions.

Black-box simulators remain out of the near-term route. They may be optional
demonstration or industry-facing validation later, but they should not be the
first HF0 implementation target.

## M2476 Scope

M2476 should audit dependency/API feasibility only. It should answer:

```text
1. Which external backend family is the primary candidate?
2. Can its dependency, licensing, and build boundary be audited locally?
3. Is a Python-accessible or wrapper-accessible reset/step path plausible?
4. Which state fields can map to ActorView without hidden/oracle actor inputs?
5. Which diagnostics must remain artifact-only?
6. What is the smallest no-validation implementation/preflight follow-up?
```

M2476 may inspect local environment state and official/source documentation if
needed, but it must not install packages, import external high-fidelity
simulation modules, run external simulation, or claim validation readiness.

## Backend Admission Criteria

An external backend route is admissible only if the next implementation can
preserve:

```text
actor observation shape: 72
actor action shape: 3
P0ObservationExtractor input: ActorView only
hidden/oracle/solver/tire/contact data: diagnostics only
```

Required actor-visible fields:

```text
ego response:
  vx_body, vy_body, yaw_rate, ax_body, ay_body

actuator response:
  steer angle normalized by max steer
  steer rate normalized by max steer rate
  throttle state in [0, 1]
  brake state in [0, 1]
  previous steer/throttle/brake commands

scene geometry:
  8 left road-boundary body-frame points
  8 right road-boundary body-frame points
  4 obstacle slots with geometry and relative motion
```

Forbidden actor-visible fields:

```text
friction coefficient or hidden dynamics parameters
tire force, slip, load, or solver convergence signals
oracle obstacle feasibility labels
reference trajectory, TTC, path error, target beta, or progress answer
reward terms, success labels, or validation labels
```

External backend diagnostics may record those values for artifacts and audits,
but the P0 extractor must not read them.

## Next Implementation Shape

If M2476 passes dependency/API audit, the first implementation should still be
bounded:

```text
external backend adapter scaffold
no measured validation
no policy rollout
no training
no ranking
no winner selection
single reset/step smoke or synthetic-state adapter fixture only
```

The first external smoke should prove only:

```text
reset produces ActorView-compatible deployable state
step accepts action shape 3
P0 extraction returns shape 72
diagnostics remain separated
failure/status taxonomy is recorded
```

If M2476 does not pass dependency/API audit, route to the source-only
four-wheel adapter preflight instead of weakening the actor contract or jumping
to validation.

## Evidence Scope

M2475 is route design only. It converts M2472-M2474 interface evidence into a
bounded external-backend audit route.

M2475 does not establish high-fidelity validation readiness, driver
performance, current-sim benchmark readiness, finite-window-vs-GRU evidence, or
level-3 self-identification.

## Next

Route to `m2476-high-fidelity-interface-external-backend-dependency-api-audit`.
