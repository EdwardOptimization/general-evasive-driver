# Current Status

This file is the compact official state for the project. Milestone documents
and `docs/research-log.md` remain the detailed experiment log.

## Project Identity

- Repository: `general-evasive-driver`
- Current Python package name: `autodrift`
- Working title: General Evasive Driver
- Core direction: closed-loop RL driver for handling-limit emergency avoidance,
  with drift as one possible maneuver rather than the project identity.

## Current Research Blocker

Latest completed milestone:

```text
m2477-high-fidelity-interface-preparation-branch-synthesis
```

Latest attempted milestone:

```text
m2477-high-fidelity-interface-preparation-branch-synthesis
result: completed
```

Current next task:

```text
m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight
```

Current route:

```text
M2477 completed the high-fidelity interface preparation branch synthesis after
the validator enforced a non-evidence milestone cadence stop. The synthesis
continues the branch only to executable source-only four-wheel adapter
evidence, not to another dependency/design-only milestone.
```

The Chrono-family route remains plausible but conditional because the active
local environment does not have `pychrono` or `projectchrono` installed and
this branch currently forbids external simulator installation, import, or
execution. The synthesis therefore routes to source-only `FourWheelDriftModel`
HF0 adapter preflight as the next bounded executable step.

M2477 did not install, import, or run an external high-fidelity simulator. It
did not run measured validation, policy evaluation, training, replay, PPO,
controller ranking, winner selection, or any paper/FW-vs-GRU/self-ID/current-
sim/high-fidelity validation verdict.

The active next task is M2478: implement the source-only four-wheel model
through the HF0 adapter boundary. M2478 must preserve P0 observation shape
`72`, action shape `3`, and diagnostics separation. It must not install,
import, or run external high-fidelity simulation, train, rank controllers,
select winners, or make validation/paper verdict claims.

## Latest Evidence

M2471 remains the active route pivot after the post-M2470 synthesis:

```text
decision:
  freeze current-sim as a diagnostic/mining layer
  stop direct static current-sim materialization as the immediate route
  start high-fidelity interface preparation now
```

Current-sim scenario-readiness evidence remains useful but not driver
capability evidence:

```text
M2468 reset-only attempts: 120
M2468 reset successes: 109
stable_aes_support: 14/24
stable-AES failures: 10/11 total reset failures
partial stable-AES cells:
  broad threshold-free: 5/8
  threshold-band: 3/8
  low-mu near: 6/8
```

HF0 interface evidence now consists of:

```text
M2472:
  design: DynamicsBackend boundary and P0 extractor contract

M2473:
  result_class: hf0_contract_preflight_pass
  reset observation shape: 72
  step observation shape: 72
  action shape: 3
  actor/action contract changed: false
  hidden/oracle diagnostics enter actor input: false

M2474:
  result_class: current_sim_adapter_smoke_pass
  backend: current_sim_autodrift_hf0
  seed count: 3
  bounded reset count: 3
  bounded step count: 6
  observation/action shape: 72 / 3
  max extractor parity error: 5.960464477539063e-08
  actor/action contract changed: false
  hidden/oracle diagnostics enter actor input: false

M2475:
  decision: external_backend_route_to_dependency_api_audit
  primary direction: open auditable high-fidelity backend route
  fallback direction: source-only four-wheel adapter preflight
  external simulation installed/imported/executed: false

M2476:
  decision: conditional_external_backend_route_to_branch_synthesis
  local pychrono/projectchrono package: absent
  Chrono route: plausible but conditional
  next route: branch synthesis before source-only adapter preflight
  external simulation installed/imported/executed: false

M2477:
  synthesis decision: continue
  decision: continue_to_source_only_four_wheel_adapter_preflight
  process-overhead risk: high
  supported driver/paper evidence: none
  next executable route: source-only FourWheelDriftModel HF0 adapter preflight
  external simulation installed/imported/executed: false
```

## Current Interpretation Boundary

Allowed claim:

```text
The HF0 interface boundary has checked local contract primitives, a current-sim
adapter smoke, a bounded external-backend route design, a dependency/API audit,
and branch synthesis. These preserve the canonical P0 actor/action contract and
keep diagnostics outside actor input, but they do not prove driver capability.
```

Blocked claims:

```text
high-fidelity validation readiness
driver performance improvement
current-sim benchmark readiness
controller-family ranking
winner selection
paper-level benchmark evidence
finite-window vs GRU conclusion
level3 self-identification evidence
scenario redesign success
training repair success
```

## Immediate Next Step

M2478 should implement the source-only four-wheel adapter preflight from:

```text
docs/m2472-high-fidelity-interface-hf0-design.md
docs/m2476-high-fidelity-interface-external-backend-dependency-api-audit.md
docs/m2477-high-fidelity-interface-preparation-branch-synthesis.md
src/autodrift/four_wheel_dynamics.py
src/autodrift/high_fidelity_interface.py
```

The preflight must expose only `ActorView` to `P0ObservationExtractor`, return
observation shape `72`, accept action shape `3`, and keep four-wheel force,
slip/load-like, fault, and hidden dynamics values in diagnostics only. It must
not install, import, or run external high-fidelity simulation, execute policy
rollout beyond bounded adapter smoke steps, train, replay, use PPO, rank
controllers, select a winner, or claim high-fidelity validation, current-sim
verdict, paper-level evidence, finite-window-vs-GRU evidence, or level-3
self-identification.
