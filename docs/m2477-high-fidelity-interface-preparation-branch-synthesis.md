# M2477 High-Fidelity Interface Preparation Branch Synthesis

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_source_only_four_wheel_adapter_preflight`
- manifest: `experiments/manifests/m2477-high-fidelity-interface-preparation-branch-synthesis.json`
- synthesis artifact: `docs/m2477-high-fidelity-interface-preparation-branch-synthesis.md`
- parent evidence window: `m2471` through `m2476`
- next milestone: `m2478-high-fidelity-interface-source-only-four-wheel-adapter-preflight`
- external high-fidelity simulation installed/imported/executed in M2477: `false`
- measured validation/policy evaluation/training/replay/PPO/ranking/winner selection in M2477: `false`
- paper/FW-vs-GRU/level3 self-ID/current-sim/high-fidelity validation verdict claims: `false`

## Evidence Summary

M2471 pivoted the project away from another static current-sim
materialization/audit chain and opened a high-fidelity interface preparation
branch. M2472-M2476 then produced the following evidence:

```text
M2472:
  HF0 design
  DynamicsBackend reset/step/close boundary
  ActorView/P0ObservationExtractor design
  no simulation, reset, rollout, policy action, training, ranking, verdict

M2473:
  HF0 contract implementation/preflight
  reset observation shape: 72
  step observation shape: 72
  action shape: 3
  P0 extractor shape: 72
  hidden/oracle diagnostics enter actor input: false
  external high-fidelity required/imported/run: false

M2474:
  current-sim adapter smoke through HF0 backend
  seed count: 3
  bounded reset count: 3
  bounded step count: 6
  observation/action shape: 72 / 3
  max extractor parity error: 5.960464477539063e-08
  hidden/oracle diagnostics enter actor input: false
  external high-fidelity required/imported/run: false

M2475:
  external-backend route design
  primary candidate direction: open auditable high-fidelity vehicle backend
  preferred family: Chrono/Chrono::Vehicle
  fallback: source-only FourWheelDriftModel adapter preflight
  no install/import/simulation

M2476:
  external dependency/API audit
  local Python/CMake/conda/g++/ninja/git available
  local pychrono/projectchrono package: absent
  Chrono route: plausible but conditional
  next route must synthesize before more interface milestones
```

This branch changed workflow and infrastructure capability. It did not produce
driver capability evidence or paper evidence.

## Supported Claims

Supported:

```text
HF0 actor/action contracts are now machine-checkable in local code.

The canonical P0 actor observation shape remains 72.

The deployed action contract remains shape 3 with steer/throttle/brake mapping.

Hidden dynamics, oracle labels, reward terms, solver/backend values, and
diagnostics remain outside ActorView and outside P0ObservationExtractor input.

Current-sim can be wrapped through the HF0 boundary while preserving P0 parity.

Chrono-family external backend work is plausible from official/source API
evidence, but it is conditional on dependency and wrapper decisions.

The branch should continue only if the next milestone produces executable
adapter evidence rather than another dependency/design-only artifact.
```

## Falsified Claims

Falsified or still blocked:

```text
High-fidelity validation readiness:
  blocked. No external high-fidelity backend is installed, imported, run, or
  smoke-tested.

Chrono backend is locally ready:
  blocked. pychrono/projectchrono is absent in the active environment.

Driver capability improved:
  unsupported. No policy action, rollout, training, replay, benchmark, or
  promotion gate ran in M2471-M2477.

Current-sim verdict improved:
  unsupported. Current-sim remains a diagnostic/mining layer, and M2474 used
  only bounded adapter smoke steps.

Finite-window-vs-GRU or level-3 self-ID evidence:
  unsupported. No history-necessity comparison or recurrent belief proof ran.

The branch can add another design/audit milestone without synthesis:
  false. The validator correctly caught the non-evidence milestone cadence.
```

## Failure Taxonomy Summary

Observed or active:

```text
lineage_invalid risk:
  controlled by manifests and review artifacts. No actor/action contract
  migration is allowed without explicit new gates.

contract_violation risk:
  controlled by M2473/M2474 shape and diagnostics flags. No violation observed.

metric_artifact risk:
  high if bounded adapter smoke is misrepresented as validation. Current docs
  keep it infrastructure-only.

scenario_sampling_failure:
  inherited from the current-sim stable-AES branch. Not addressed by HF0.

dependency/API blocker:
  active. Chrono-family route is plausible but not locally executable because
  no pychrono/projectchrono package is present and installation/import is
  forbidden in the audited milestones.

process-overhead risk:
  high. M2472-M2477 are mostly design/audit/interface milestones. M2474 is the
  only executable adapter smoke.
```

Not observed:

```text
private holdout contamination
checkpoint promotion without proof/generalization
controller-family ranking
winner selection
actor input oracle leakage
```

## Public Gate Overfit Risk

Risk before M2477: `medium`.

Reason:

```text
The branch avoided optimizing public current-sim rows, but it accumulated
interface/process milestones. Without synthesis, the next adapter task would
look productive while preserving a design-only loop.
```

Risk after M2477: `medium-low` if the next milestone is executable adapter
evidence.

Mitigation:

```text
Continue only to source-only FourWheelDriftModel HF0 adapter preflight.

Do not add another external dependency route design or audit before producing
adapter evidence.

Keep all adapter results in infrastructure scope and forbid high-fidelity
validation or driver-performance claims.
```

Residual risk:

```text
Source-only FourWheelDriftModel is not a high-fidelity simulator. It can improve
adapter and four-contact-patch evidence, but it cannot establish external
high-fidelity validation readiness.
```

## Next Branch Decision

Decision:

```text
continue_to_source_only_four_wheel_adapter_preflight
```

Rationale:

```text
Stopping now would leave the branch at dependency/API audit with no executable
four-wheel adapter evidence.

Continuing directly to Chrono adapter implementation is not admissible because
the local external backend dependency is absent and installation/import is
outside the allowed gate.

Continuing to source-only FourWheelDriftModel HF0 adapter preflight is bounded,
executable, and aligned with the real objective: it exercises a richer dynamics
source through the same deployable actor/action contract without oracle inputs.
```

Required next constraints:

```text
M2478 must preserve observation shape 72 and action shape 3.
M2478 must keep per-wheel forces, slip/load-like state, fault scales, and
hidden dynamics out of ActorView.
M2478 must generate a summary artifact and focused tests.
M2478 must not install, import, or run external high-fidelity simulation.
M2478 must not claim high-fidelity validation readiness, driver performance,
paper evidence, finite-window-vs-GRU evidence, or level-3 self-identification.
```

## Evidence Scope

M2477 is process synthesis. It supports continuing the HF interface branch to a
bounded executable source-only adapter preflight. It does not support driver
performance, high-fidelity validation, paper evidence, finite-window-vs-GRU, or
self-identification claims.
