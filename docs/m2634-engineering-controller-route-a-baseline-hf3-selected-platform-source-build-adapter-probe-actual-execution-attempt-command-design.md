# M2634 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Actual Execution Attempt Command Design

- status: completed
- decision: `route_to_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt_preflight`
- manifest: `experiments/manifests/m2634-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-actual-execution-attempt-command-design.json`
- parent synthesis: `docs/m2633-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-result-synthesis.md`
- parent audit: `docs/m2632-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-materialization-result-audit.md`
- parent materialization summary: `runs/m2631_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_attempt/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-preflight.json`
- next: `m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-preflight`

## Design Verdict

M2634 converts the accepted M2631/M2632/M2633 selected-platform
source-build/adapter-probe execution-attempt protocol into a concrete future
command-attempt bundle. The bundle is deliberately gated: M2635 must first
record local source availability, tool availability, and dependency boundaries
before any configure, compile, adapter import, or backend metadata probe command
is attempted.

This is still command design. M2634 does not install or import external
high-fidelity simulation packages, mutate dependencies, mutate source trees,
use network dependency resolution, run source builds, run adapter probes, start
backends, reset or step environments, execute policy actions, roll out, replay,
validate, train, rank controllers, promote checkpoints, compute success rates,
or claim driver performance.

If M2635 executes the designed bundle, its supported claim will be limited to
either a bounded local/no-network command-attempt record or an explicit
source/tool/dependency blocker. A successful configure or compile attempt would
still require result audit before any dependency readiness, backend discovery,
backend availability, reset feasibility, validation readiness, validation
result, high-fidelity validation, paper evidence, finite-window-vs-GRU, current
sim verdict, self-ID, or driver-performance claim.

## Route Interpretation

`docs/post-m2470-route-plan.md` remains the governing route document. Route C
requires preparing a validation layer without waiting for current-sim to become
perfect, while keeping current-sim diagnostic and avoiding hidden/oracle actor
inputs. It also favors an open/auditable high-fidelity vehicle layer such as a
Chrono-family backend.

M2634 applies that route literally:

```text
selected platform family: chrono_vehicle_or_equivalent_open_backend
command scope: source-build and adapter-probe actual execution-attempt bundle
execution scope in M2634: none
future execution scope in M2635: bounded local/no-network attempt only
validation scope: none
driver-performance scope: none
```

This prevents another static current-sim artifact from becoming the next loop.
It also prevents the opposite error: jumping directly from protocol rows to
backend or validation claims without local command evidence.

## Current Local Availability Audit

Read-only checks were performed before this design. They did not execute a
source build, adapter probe, backend start, reset, step, rollout, replay, or
validation.

Observed local state:

```text
repo-local third_party/external/vendor/chrono/Chrono/pychrono/build dirs at maxdepth 2: none
pychrono Python module discoverable: false
projectchrono Python module discoverable: false
Python: 3.12.12
cmake: 3.28.3
ninja: 1.13.0.git.kitware.jobserver-pipe-1
c++: 13.3.0
pyproject.toml / environment*.yml pychrono or projectchrono dependency entry: none
```

This matches the M2476 dependency audit boundary: Chrono is an open/auditable
candidate route from official/source references, but the local environment does
not prove an installed or importable Chrono backend.

Repo-local adapter evidence is available only in the source-only sense:

```text
implementation: src/autodrift/four_wheel_hf0_adapter.py
tests: tests/test_four_wheel_hf0_adapter.py
M2478 summary: runs/m2478_high_fidelity_interface_source_only_four_wheel_adapter_preflight/summary.json
M2592 boundary: source-only adapter blocker closure materialized in repo-local adapter-evidence sense only
```

That source-only adapter can be used for a metadata-only local adapter import
probe, but it cannot be upgraded into Chrono availability or high-fidelity
validation evidence.

## Command Roots

M2635 should use these roots exactly unless an explicit manifest repair changes
them:

```text
repo cwd: /home/quyaonan/workspace/autodrift
RUN_DIR: runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt
LOG_DIR: ${RUN_DIR}/logs
ARTIFACT_DIR: ${RUN_DIR}/artifacts
SOURCE_ROOT: ${AUTODRIFT_HF3_CHRONO_SOURCE_ROOT:-/home/quyaonan/workspace/chrono}
BUILD_ROOT: ${RUN_DIR}/build/chrono
PYTHONPATH: src
OMP_NUM_THREADS: 1
MKL_NUM_THREADS: 1
```

All generated files must stay under `RUN_DIR`. The selected-platform source
tree, if present, must be read-only from the harness perspective. Configure and
compile commands may write only to `BUILD_ROOT`; they must not write into
`SOURCE_ROOT`.

## Availability Gate

M2635 must run the availability checks before any configure, compile, adapter
import, or backend metadata probe attempt. Each check must have separate
stdout/stderr capture and a return-code row.

```text
cwd: /home/quyaonan/workspace/autodrift
timeout: 30s per check
stdout/stderr: ${LOG_DIR}/availability.<check>.stdout and .stderr
summary rows: ${RUN_DIR}/source_availability_rows.csv
```

Required checks:

```text
test -d "$SOURCE_ROOT"
test -f "$SOURCE_ROOT/CMakeLists.txt"
cmake --version
ninja --version
c++ --version
python -c "import importlib.util; print('pychrono', importlib.util.find_spec('pychrono') is not None); print('projectchrono', importlib.util.find_spec('projectchrono') is not None)"
```

Return-code interpretation:

```text
source root missing:
  classify as dependency_source_unavailable
  do not run configure compile adapter import backend metadata probe

CMakeLists.txt missing:
  classify as selected_platform_source_schema_unavailable
  do not run configure compile adapter import backend metadata probe

cmake/ninja/c++ unavailable:
  classify as local_toolchain_unavailable
  do not run configure compile adapter import backend metadata probe

pychrono/projectchrono unavailable:
  record as package_import_unavailable only
  do not install packages and do not treat absence as Chrono source-build failure
```

## Source-Build Configure Attempt

This command is allowed only if the availability gate proves that `SOURCE_ROOT`
exists, `SOURCE_ROOT/CMakeLists.txt` exists, and the local toolchain commands
are present.

```text
name: source_build_configure_attempt
cwd: /home/quyaonan/workspace/autodrift
timeout: 300s
stdout: ${LOG_DIR}/source_build_configure.stdout
stderr: ${LOG_DIR}/source_build_configure.stderr
artifact root: ${BUILD_ROOT}
command:
  cmake -S "$SOURCE_ROOT" -B "$BUILD_ROOT" -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF -DCH_ENABLE_MODULE_VEHICLE=ON -DCH_ENABLE_MODULE_PYTHON=OFF
```

Return-code interpretation:

```text
0:
  configure_attempt_executed true
  configure_returncode_zero true
  configure_success_candidate true pending M2636 audit

nonzero or timeout:
  configure_attempt_executed true
  configure_returncode_zero false
  route to configure_failure_result_audit_or_repair
  do not run compile
```

Even return code `0` does not imply dependency execution readiness, backend
discovery, backend availability, reset feasibility, validation readiness, or
driver performance.

## Source-Build Compile Attempt

This command is allowed only after a return-code-zero configure attempt.

```text
name: source_build_compile_attempt
cwd: /home/quyaonan/workspace/autodrift
timeout: 1200s
stdout: ${LOG_DIR}/source_build_compile.stdout
stderr: ${LOG_DIR}/source_build_compile.stderr
artifact root: ${BUILD_ROOT}
command:
  cmake --build "$BUILD_ROOT" --parallel 2
```

Return-code interpretation:

```text
0:
  compile_attempt_executed true
  compile_returncode_zero true
  compile_success_candidate true pending M2636 audit

nonzero or timeout:
  compile_attempt_executed true
  compile_returncode_zero false
  route to compile_failure_result_audit_or_repair
  do not claim backend discovery or availability
```

Compile output is a build artifact only. It must not be installed into the
Python or system environment, and it must not mutate `SOURCE_ROOT`.

## Adapter Import Attempt

M2635 may run a metadata-only import of the repo-local HF0 adapter module after
the availability gate. This is not an external simulator import and not a
Chrono adapter proof. It exists only to confirm that the current repo-local
adapter surface is importable before a later external adapter exists.

```text
name: repo_local_adapter_import_metadata_attempt
cwd: /home/quyaonan/workspace/autodrift
timeout: 60s
env: PYTHONPATH=src
stdout: ${LOG_DIR}/adapter_import.stdout
stderr: ${LOG_DIR}/adapter_import.stderr
trace: ${ARTIFACT_DIR}/adapter_import_trace.json
command:
  PYTHONPATH=src python -c "import importlib; m=importlib.import_module('autodrift.four_wheel_hf0_adapter'); print({'adapter_module': m.__name__, 'probe_only': True, 'external_sim_imported': False, 'backend_started': False})"
```

Return-code interpretation:

```text
0:
  repo_local_adapter_import_attempt_executed true
  repo_local_adapter_import_returncode_zero true
  adapter_import_success_candidate true pending M2636 audit

nonzero or timeout:
  repo_local_adapter_import_attempt_executed true
  repo_local_adapter_import_returncode_zero false
  route to adapter_import_repair
```

This command must not import `pychrono`, `projectchrono`, Chrono shared
libraries, or other external high-fidelity simulation packages. It must not
instantiate a backend, reset, step, roll out, replay, or validate.

## Backend Metadata Probe Attempt

M2635 may run a metadata-only class probe of the repo-local adapter. It must
not instantiate the class because instantiation creates a model object and can
be confused with a backend start in later audits.

```text
name: repo_local_backend_metadata_probe_attempt
cwd: /home/quyaonan/workspace/autodrift
timeout: 60s
env: PYTHONPATH=src
stdout: ${LOG_DIR}/backend_metadata_probe.stdout
stderr: ${LOG_DIR}/backend_metadata_probe.stderr
trace: ${ARTIFACT_DIR}/backend_probe_trace.json
command:
  PYTHONPATH=src python -c "from autodrift.four_wheel_hf0_adapter import FourWheelHF0Backend; print({'backend_class': FourWheelHF0Backend.__name__, 'backend_id': getattr(FourWheelHF0Backend, 'backend_id', None), 'metadata_probe_only': True, 'backend_started': False, 'reset_executed': False, 'step_executed': False})"
```

Return-code interpretation:

```text
0:
  backend_metadata_probe_attempt_executed true
  backend_metadata_probe_returncode_zero true
  metadata_probe_success_candidate true pending M2636 audit

nonzero or timeout:
  backend_metadata_probe_attempt_executed true
  backend_metadata_probe_returncode_zero false
  route to backend_probe_repair
```

This metadata probe cannot support backend discovery, backend availability,
reset feasibility, rollout feasibility, validation readiness, validation
result, or performance claims.

## Artifact Capture Contract

M2635 should write these artifacts:

```text
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/summary.json
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/command_plan.json
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/environment_snapshot.txt
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/source_availability_rows.csv
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/command_attempt_rows.csv
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/artifact_manifest.csv
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/backend_probe_trace.json
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/backend_probe_trace_rows.csv
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/claim_boundary_checks.csv
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/gate_matrix.csv
docs/m2635-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-preflight.md
```

`summary.json` must distinguish:

```text
availability_gate_executed
source_root_available
toolchain_available
configure_attempt_executed
compile_attempt_executed
repo_local_adapter_import_attempt_executed
repo_local_backend_metadata_probe_attempt_executed
external_simulator_imported
backend_started
reset_executed
step_executed
rollout_executed
validation_executed
driver_performance_claim_allowed
```

## Abort Routes

M2635 must abort forward execution and write an auditable blocker row in these
cases:

```text
source root missing:
  route to dependency/source availability blocker

source root lacks CMakeLists.txt:
  route to platform-source schema repair

cmake/ninja/c++ unavailable:
  route to local toolchain availability blocker

configure nonzero or timeout:
  route to configure failure audit or source build repair

compile nonzero or timeout:
  route to compile failure audit or source build repair

repo-local adapter import nonzero or timeout:
  route to adapter import repair

metadata probe nonzero or timeout:
  route to backend metadata probe repair

any network use, install attempt, dependency mutation, source-tree mutation,
external simulator import, backend start, reset, step, rollout, replay,
validation, training, ranking, winner selection, success-rate computation, or
driver-performance claim:
  fail the milestone as contract_violation
```

## Actor And Action Boundary

The deployed contract remains:

```text
actor observation shape: 72
actor action shape: 3
action mapping: [steer, throttle, brake]
hidden/oracle actor inputs: false
taxonomy labels actor-visible: false
backend statuses actor-visible: false
build/probe/reset/validation outcomes actor-visible: false
selected platform or protocol status actor-visible: false
rule-switching controller mode: false
```

The command-attempt harness may record backend and build diagnostics in
artifacts, but none of those fields may enter actor input or be treated as a
controller feature.

## Supported Claims

M2634 supports only:

```text
M2634 designed a bounded local/no-network selected-platform source-build and
adapter-probe actual execution-attempt command bundle.

M2634 registered M2635 as the follow-up bounded actual execution-attempt
preflight with explicit availability gates, logs, artifacts, return-code
interpretation, claim boundaries, and abort routes.

Current live read-only audit shows no repo-local Chrono source root and no
discoverable pychrono/projectchrono Python module; therefore M2635 must record
source/dependency availability before attempting configure/compile/probe.
```

## Rejected Claims

M2634 rejects:

```text
dependency execution readiness
source-build attempt execution
source-build execution or success
adapter-probe attempt execution
adapter-probe execution or success
external simulator import
backend discovery
backend availability
backend start
reset execution
reset success
step execution
rollout feasibility
rollout execution
replay execution
validation protocol readiness
validation admission
validation readiness
validation result
success-rate or controller-family verdict metrics
ranking or winner selection
checkpoint promotion
driver performance
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
level3 self-identification
```

## M2635 Handoff

M2635 should implement and execute the bounded actual execution-attempt
preflight only within the guard rails above. Its primary success artifact is:

```text
runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/summary.json
```

Allowed M2635 outcomes:

```text
bounded_actual_execution_attempt_artifacts_written
dependency_source_unavailable_blocker_recorded
selected_platform_source_schema_unavailable_blocker_recorded
local_toolchain_unavailable_blocker_recorded
configure_failure_recorded
compile_failure_recorded
repo_local_adapter_import_repair_needed
backend_metadata_probe_repair_needed
contract_violation_failed
```

If M2635 writes a complete command-attempt record, M2636 should audit the
result before any reset feasibility, validation admission, validation result,
backend availability, or driver-performance interpretation.
