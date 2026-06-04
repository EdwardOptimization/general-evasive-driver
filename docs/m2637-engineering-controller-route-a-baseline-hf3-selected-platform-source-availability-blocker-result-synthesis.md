# M2637 Engineering Controller Route A Baseline HF3 Selected-Platform Source Availability Blocker Result Synthesis

- status: completed
- synthesis decision: `pivot_to_dependency_source_blocker_report_and_user_supplied_source_contract`
- manifest: `experiments/manifests/m2637-engineering-controller-route-a-baseline-hf3-selected-platform-source-availability-blocker-result-synthesis.json`
- parent audit: `docs/m2636-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-result-audit.md`
- parent summary: `runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.json`
- next: `m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design`

## Evidence Summary

The post-M2470 route plan moved high-fidelity validation into Route C so that
current-sim readiness work would stop becoming the project's main loop. Route C
allows HF0/HF1/HF2 interface preparation and then an HF3 low-cost pilot only
after the high-fidelity backend path can be audited without hidden actor inputs
or validation/performance overclaiming.

M2635/M2636 reached the first bounded local/no-network selected-platform
source-build and adapter-probe command-attempt gate. The selected platform
family remained `chrono_vehicle_or_equivalent_open_backend`, but the configured
source root `/home/quyaonan/workspace/chrono` was not present in the current
local environment. `CMake`, `Ninja`, and `c++` were available, while the source
root and its `CMakeLists.txt` were unavailable and `pychrono`/`projectchrono`
package discovery did not find an importable package.

The accepted M2635 result is therefore not a build result and not an adapter or
backend result. It is a dependency/source availability blocker:

```text
status_pass: true
result_class: dependency_source_unavailable_blocker_recorded
source_root_available: false
cmake_lists_available: false
toolchain_available: true
package_import_unavailable: true
availability_blocker: dependency_source_unavailable
source_availability_rows: 6
command_attempt_rows: 4
backend_probe_trace_rows: 2
claim_boundary_rows: 27
artifact_manifest_rows: 11
gates: 9
```

Because the source root was absent, configure, compile, repo-local adapter
import metadata probe, and backend metadata probe attempts were all skipped
with `dependency_source_unavailable`. No external dependency was installed or
imported, no source tree was mutated, no network access was used, no backend was
started, and no reset, step, rollout, replay, validation, training, ranking, or
performance computation was executed.

The actor/action contract remains intact:

```text
actor_observation_shape: 72
action_shape: 3
deployed_action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_detected: false
metadata_actor_visible: false
```

## Supported Claims

M2637 supports only these operational claims:

```text
M2635/M2636 produced valid local/no-network blocker evidence.

The current local environment does not contain the configured selected-platform
source root /home/quyaonan/workspace/chrono.

The local toolchain is present enough that the blocker is source/dependency
availability rather than CMake/Ninja/C++ availability.

The selected-platform build/probe route cannot proceed to actual configure,
compile, adapter probe, backend metadata probe, reset feasibility, validation,
or performance interpretation until source availability is repaired or the
source dependency is explicitly supplied.

The branch must pivot from static selected-platform preparation to a dependency
source blocker report and user-supplied source contract.
```

## Falsified Claims

M2637 falsifies or refuses the following interpretations for the current local
state:

```text
The selected-platform source-build route is ready to execute.
The selected-platform adapter-probe route is ready to execute.
M2635 demonstrated a source-build failure.
M2635 demonstrated an adapter-probe failure.
M2635 demonstrated backend discovery failure.
M2635 demonstrated backend unavailability.
M2635 demonstrated reset feasibility or reset failure.
M2635 granted validation admission.
M2635 produced validation results.
M2635 produced driver-performance evidence.
Another static HF3 source-build/adapter-probe preparation artifact can change
the next admission decision without repairing source availability.
```

The source blocker also does not affect paper-route claims. M2637 does not
support finite-window-vs-GRU evidence, current-sim verdicts, high-fidelity
validation verdicts, level3 self-identification, controller ranking, winner
selection, checkpoint promotion, or deployment readiness.

## Failure Taxonomy Summary

Accepted blocker:

```text
dependency_source_unavailable
```

Not accepted as active failures:

```text
contract_violation
lineage_invalid
metric_artifact
scenario_sampling_failure
behavior_regression
objective_overfit as a result claim
local_toolchain_unavailable
configure_failure_recorded
compile_failure_recorded
adapter_import_repair_needed
backend_metadata_probe_repair_needed
backend_unavailable
validation_failure
driver_performance_failure
```

The process risk remains medium-high. M2584-M2637 produced useful Route C
interface and blocker hygiene, but it is still validation-layer process
evidence rather than closed-loop driver capability. Continuing with another
static design/materialization/audit step on the same missing source dependency
would turn the blocker into local search.

## Public Gate Overfit Risk

Public gate overfit risk is high enough to force a pivot. The recent HF3 branch
has repeatedly improved readiness and boundary bookkeeping, but M2635 supplied
a real environmental blocker: the selected-platform source dependency is not
available. Once that blocker is accepted, more static HF3 source-build or
adapter-probe scaffolding cannot change the next Route C admission decision.

The public-gate-safe path is to make the blocker explicit and define the exact
source provision contract before any further build/probe attempt. That keeps
Route C auditable without pretending that missing dependency evidence is
high-fidelity validation progress.

## Next Branch Decision

Decision:

```text
pivot_to_dependency_source_blocker_report_and_user_supplied_source_contract
```

The current selected-platform execution path is paused at the source
availability boundary. It should not proceed to configure, compile,
repo-local adapter import, backend metadata probe, reset feasibility,
validation admission, or performance interpretation until a source root or
package dependency is explicitly supplied through a new manifest.

Next route:

```text
m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design
```

M2638 must write a blocker report and contract document. It should specify the
accepted source provision inputs, such as a user-supplied local source root or
an explicitly approved dependency/package path, and the minimum files or import
surface required before any renewed local/no-network availability preflight can
run.

M2638 must not fetch, install, import, build, probe, start a backend, reset,
step, roll out, replay, validate, train, rank, promote, compute success rates,
or make driver-performance claims. If no source dependency is supplied after
the blocker report, the selected-platform HF3 execution path remains paused and
the project should shift effort back to Route A engineering baseline packaging
or another explicitly registered non-HF3 branch.
