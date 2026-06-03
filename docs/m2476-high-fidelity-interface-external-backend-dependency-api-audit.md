# M2476 High-Fidelity Interface External Backend Dependency API Audit

- status: completed
- decision: `conditional_external_backend_route_to_branch_synthesis`
- manifest: `experiments/manifests/m2476-high-fidelity-interface-external-backend-dependency-api-audit.json`
- parent route design: `docs/m2475-high-fidelity-interface-external-backend-route-design.md`
- parent adapter smoke: `docs/m2474-high-fidelity-interface-current-sim-adapter-smoke.md`
- next milestone: `m2477-high-fidelity-interface-preparation-branch-synthesis`
- external high-fidelity simulation installed/imported/executed in M2476: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2476: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Purpose

M2476 audits whether the selected external backend direction can move into
implementation without breaking HF0 constraints. This milestone does not
install, import, or run an external high-fidelity simulator.

The audited HF0 admission boundary remains:

```text
actor observation shape: 72
actor action shape: 3
P0ObservationExtractor input: ActorView only
hidden/oracle/solver/tire/contact data: diagnostics only
```

## Sources

Official/source references used for this audit:

```text
Project Chrono documentation:
  https://api.projectchrono.org/
  https://api.projectchrono.org/pychrono_introduction.html
  https://api.projectchrono.org/pychrono_installation.html
  https://api.projectchrono.org/structchrono_1_1vehicle_1_1_driver_inputs.html
  https://api.projectchrono.org/vehicle_driver.html
  https://api.projectchrono.org/classchrono_1_1vehicle_1_1_ch_vehicle.html

Project Chrono source repository:
  https://github.com/projectchrono/chrono
```

Audit interpretation from those sources:

```text
1. Chrono is open-source and has C++ and Python APIs.
2. PyChrono is the documented Python interface.
3. The documented Python installation route includes conda packages.
4. Chrono::Vehicle exposes driver inputs and vehicle advance/synchronize style
   integration surfaces.
5. DriverInputs already separates steering, throttle, and braking channels.
```

Those facts make a Chrono-family route plausible. They do not prove that the
local machine has an installed or importable Chrono backend.

## Local Read-Only Environment Audit

Commands run:

```text
python --version
command -v conda
command -v cmake && cmake --version | head -n 1
g++ --version | head -n 1
ninja --version
git --version
python -m pip show pychrono projectchrono
conda list pychrono
```

Observed local state:

```text
Python: 3.12.12
conda: /home/quyaonan/miniforge3/bin/conda
cmake: /usr/bin/cmake, version 3.28.3
g++: 13.3.0
ninja: 1.13.0.git.kitware.jobserver-pipe-1
git: 2.43.0
pip pychrono/projectchrono package: not found
conda pychrono package in active environment: not found
```

No external simulator package was installed, imported, or executed.

## API Mapping Audit

Chrono/Chrono::Vehicle appears API-plausible for HF0 because:

```text
driver input mapping:
  HF0 steer normalized [-1, 1]
    -> Chrono steering driver input
  HF0 physical throttle [0, 1]
    -> Chrono throttle driver input
  HF0 physical brake [0, 1]
    -> Chrono braking driver input

simulation progression:
  DynamicsBackend.reset
    -> future wrapper builds/initializes system and vehicle state
  DynamicsBackend.step(action)
    -> future wrapper maps action to DriverInputs, synchronizes, advances,
       and extracts actor-visible state

actor-visible ego response:
  position/orientation are backend state only unless needed for body-frame
  conversion
  body-frame velocity, yaw rate, and acceleration can be derived from vehicle
  state/chassis motion if exposed by the selected wrapper

diagnostics:
  tire forces, slip, contact, terrain, solver, runtime, and warnings must stay
  in diagnostics and must not enter ActorView
```

Unresolved mapping items before implementation:

```text
1. Confirm the exact Python or wrapper-accessible vehicle state getters in the
   locally selected Chrono build.
2. Confirm whether road/free-space and obstacle geometry will come from a
   scenario adapter rather than the vehicle API.
3. Confirm how actuator state and previous physical command fields are tracked
   across backend step calls.
4. Confirm installation channel and optional module availability without
   contaminating the training environment.
```

## Decision

Decision:

```text
conditional_external_backend_route_to_branch_synthesis
```

Rationale:

```text
Chrono remains the primary external-backend candidate direction because its
official/source documentation supports an open auditable vehicle-simulation
route with driver inputs and vehicle progression APIs.

However, M2476 cannot advance directly to Chrono adapter implementation because
the active local environment does not contain pychrono/projectchrono, and this
milestone forbids external simulator installation, import, or execution.

The likely next evidence-producing step is a source-only FourWheelDriftModel
HF0 adapter preflight. However, the high-fidelity interface preparation branch
has now reached the validator-enforced cadence limit for consecutive
non-evidence milestones. The next registered task must therefore be branch
synthesis, and that synthesis should decide whether to continue to source-only
four-wheel adapter evidence, pivot to scenario taxonomy mapping, or stop for
external dependency review.
```

## Recommended Post-Synthesis Scope

If M2477 synthesis continues the branch, the follow-up should implement a
bounded source-only four-wheel HF0 adapter preflight:

```text
backend:
  FourWheelDriftModel

input:
  deployed action shape 3
  same steer/throttle/brake mapping as HF0

actor output:
  ActorView only
  P0ObservationExtractor returns shape 72

scene:
  deterministic adapter fixture for road/free-space and obstacle slots

diagnostics:
  per-wheel force, slip/load-like values, fault scales, and internal model
  state remain diagnostics only
```

M2477 must not claim high-fidelity validation readiness. It is a source-only
adapter fallback preflight that keeps the branch executable while the external
Chrono route remains conditional on dependency/API decisions.

## Evidence Scope

M2476 is a dependency/API audit and route decision only. It supports:

```text
Chrono-family external backend route is plausible but not locally executable
without dependency decisions.
```

M2476 does not support:

```text
external backend installed/importable
external high-fidelity validation readiness
driver performance improvement
current-sim benchmark readiness
finite-window-vs-GRU evidence
level-3 self-identification
```

## Next

Route to `m2477-high-fidelity-interface-preparation-branch-synthesis`.
