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
m2474-high-fidelity-interface-current-sim-adapter-smoke
```

Latest attempted milestone:

```text
m2474-high-fidelity-interface-current-sim-adapter-smoke
result: completed
```

Current next task:

```text
m2475-high-fidelity-interface-external-backend-route-design
```

Current route:

```text
M2474 completed the HF0 current-sim adapter smoke selected by M2473. It wraps
AutoDriftEnv through CurrentSimDynamicsBackend, reconstructs ActorView from the
canonical P0 observation, and re-extracts the P0 frame through
P0ObservationExtractor to verify backend-boundary parity.
```

The M2474 summary reports seed count `3`, bounded current-sim reset count `3`,
bounded step count `6`, observation shape `72`, action shape `3`, P0 extractor
shape `72`, canonical P0 config `true`, and max extractor parity error
`5.960464477539063e-08`. All contract flags remain false: actor input
unchanged, action contract unchanged, hidden values excluded, oracle labels
excluded, and diagnostics unavailable to actor observation extraction.

M2474 did not import or run an external high-fidelity simulator. It did not run
measured validation, policy evaluation, training, replay, PPO, controller
ranking, winner selection, or any paper/FW-vs-GRU/self-ID/current-sim/high-
fidelity validation verdict. The current-sim reset/step counts are bounded
adapter-smoke counts only.

The active next task is M2475: design the bounded external-backend route after
HF0 contract and current-sim adapter smoke evidence. M2475 must select an
implementation/preflight route while preserving the P0 `72`-value observation
contract, the three-dimensional `[steer, throttle, brake]` action contract, and
the diagnostics/actor-input split. It must not install, import, or run external
high-fidelity simulation, train, rank controllers, select winners, or make
validation/paper verdict claims.

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
```

## Current Interpretation Boundary

Allowed claim:

```text
The HF0 interface boundary now has checked local contract primitives and a
current-sim adapter smoke that preserve the canonical P0 actor/action contract
and keep diagnostics outside actor input.
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

M2475 should design the external-backend route from:

```text
docs/post-m2470-route-plan.md
docs/m2472-high-fidelity-interface-hf0-design.md
docs/m2473-high-fidelity-interface-hf0-contract-implementation-preflight.md
runs/m2473_high_fidelity_interface_hf0_contract_implementation_preflight/summary.json
docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md
runs/m2474_high_fidelity_interface_current_sim_adapter_smoke/summary.json
```

The design must select a bounded next implementation or preflight route while
preserving P0 observation shape `72`, action shape `3`, and diagnostics
separation. It must not install, import, or run external high-fidelity
simulation, execute policy rollout, train, replay, use PPO, rank controllers,
select a winner, or claim high-fidelity validation, current-sim verdict,
paper-level evidence, finite-window-vs-GRU evidence, or level-3 self-
identification.
