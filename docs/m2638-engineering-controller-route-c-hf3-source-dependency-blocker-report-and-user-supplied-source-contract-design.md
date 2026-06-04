# M2638 Engineering Controller Route C HF3 Source Dependency Blocker Report And User-Supplied Source Contract Design

- status: completed
- decision: `pause_hf3_selected_platform_until_source_supplied_route_to_route_a_baseline_evidence_index_refresh`
- manifest: `experiments/manifests/m2638-engineering-controller-route-c-hf3-source-dependency-blocker-report-and-user-supplied-source-contract-design.json`
- parent synthesis: `docs/m2637-engineering-controller-route-a-baseline-hf3-selected-platform-source-availability-blocker-result-synthesis.md`
- parent audit: `docs/m2636-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-bounded-actual-execution-attempt-result-audit.md`
- parent summary: `runs/m2635_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_bounded_actual_execution_attempt/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2639-engineering-controller-route-a-baseline-evidence-index-refresh-materialization-preflight.json`
- next: `m2639-engineering-controller-route-a-baseline-evidence-index-refresh-materialization-preflight`

## Blocker Report

M2638 records the selected-platform HF3 execution path as blocked by missing
source/dependency availability, not by source-build failure, adapter-probe
failure, backend failure, reset failure, validation failure, or driver
performance.

Accepted facts from M2635/M2636/M2637:

```text
selected_platform_family: chrono_vehicle_or_equivalent_open_backend
configured_source_root: /home/quyaonan/workspace/chrono
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
gate_count: 9
```

Current local check for M2638:

```text
/home/quyaonan/workspace/chrono: missing
```

Because the configured source root is absent, M2635 correctly skipped
source-build configure, source-build compile, repo-local adapter import
metadata probe, and backend metadata probe attempts with
`dependency_source_unavailable`. No external dependency was installed or
imported, no source tree was mutated, no network access was used, no backend was
started, and no reset, step, rollout, replay, validation, training, ranking, or
performance computation was executed.

## User-Supplied Source Contract

A renewed HF3 selected-platform availability preflight is admitted only after
one of these source-provision routes is explicitly supplied through a new
manifest or user instruction:

```text
source_root_route:
  source_root path is provided explicitly
  source_root exists locally
  source_root contains CMakeLists.txt or an equivalent documented build entry
  source_root is not created or fetched by the preflight milestone
  out-of-tree build root is under the milestone run directory

package_route:
  package/import path is provided explicitly
  package name is provided explicitly
  metadata-only import check is allowed by the follow-up manifest
  no external simulator instance is created during availability preflight
  no backend start reset step rollout replay validation or performance path is executed
```

Minimum local evidence required before a renewed preflight can run:

```text
source_root_route:
  source_root_exists: true
  source_cmake_lists_exists_or_build_entry_documented: true
  cmake_available: true
  ninja_or_generator_available: true
  cxx_available: true

package_route:
  approved_package_name_present: true
  import_metadata_probe_allowed: true
  external_backend_start_allowed: false
  reset_step_rollout_validation_allowed: false
```

The renewed preflight must still be local/no-network unless a separate manifest
explicitly admits a dependency acquisition operation. M2638 does not admit
fetch, install, source-tree mutation, dependency mutation, external simulator
import, source build, adapter probe, backend start, reset, step, rollout,
replay, validation, training, ranking, success-rate computation, or driver
performance interpretation.

## Actor Contract Boundary

The source provision contract does not change the actor:

```text
observation_shape: 72
action_shape: 3
action_mapping: [steer, throttle, brake]
hidden_oracle_actor_input_detected: false
metadata_actor_visible: false
```

Allowed actor-visible inputs remain only human-view deployable signals:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent/history state
```

Forbidden actor-visible inputs remain hidden dynamics, labels, shortcuts, and
verdict answers, including `mu`, mass, tire stiffness, brake scale, actuator
tau, slip, tire force, feasibility labels, AEB/AES/drift labels, controller
mode, speed references, path error, heading error, path curvature, TTC,
required clearance, oracle stopping distance, reward terms, collision/success
labels, selected platform state, build outcome, probe outcome, reset outcome,
validation outcome, or blocker classification.

## Route Decision

M2638 pauses the selected-platform HF3 execution path until source dependency
evidence is supplied. The current worktree has no admitted source dependency,
so another HF3 build/probe preparation milestone would be local search rather
than movement toward the driver objective.

The immediate next route is Route A baseline evidence index refresh:

```text
m2639-engineering-controller-route-a-baseline-evidence-index-refresh-materialization-preflight
```

M2639 should materialize a current Route A evidence index from existing
artifacts:

```text
M2541 baseline and interface materialization
M2544 source-only execution readiness panel
M2505 public source-only diagnostic benchmark pack
M2548 HF0 P0 parity and actor runtime materialization
M2635-M2638 HF3 source dependency blocker chain
```

The index should identify which evidence is already present, which gaps remain
before a real evidence-expanding Route A action, and which next action is
admissible without changing actor inputs or claiming driver performance. It
must not rank controllers, select a winner, promote a checkpoint, compute a new
success-rate verdict, or claim paper/self-ID/high-fidelity validation results.

## Supported Claims

M2638 supports only:

```text
The selected-platform HF3 source dependency is unavailable in the current local
environment.

The dependency/source blocker is explicit and durable.

Renewed HF3 availability preflight requires a user-supplied local source root
or explicitly approved package route.

Until that source dependency is supplied, the active route should shift back to
Route A baseline evidence indexing rather than continuing static HF3
build/probe preparation.
```

## Rejected Claims

M2638 rejects:

```text
dependency execution readiness
source-build attempt executed
source-build success or failure
adapter-probe attempt executed
adapter-probe success or failure
backend discovery
backend availability
backend start
reset feasibility
reset execution
rollout feasibility
validation protocol readiness
validation admission
validation result
controller ranking
winner selection
checkpoint promotion
success-rate verdict
driver performance
paper evidence
finite-window-vs-GRU conclusion
current-sim verdict
high-fidelity validation readiness or result
level3 self-identification
full ideal driver completion
```

## Stop And Resume Conditions

HF3 selected-platform execution remains paused until one of these is true:

```text
user supplies a valid local source root
user supplies an explicitly approved package/import route
a future manifest admits a bounded dependency acquisition operation
the project pivots to another high-fidelity backend with its own source contract
```

If none of those happens, continuing to add selected-platform source-build or
adapter-probe static artifacts is disallowed by this blocker report. The project
should continue through Route A evidence indexing, baseline packaging, source-only
closed-loop panels, benchmark design, or another evidence-expanding branch that
preserves the deployable actor contract.
