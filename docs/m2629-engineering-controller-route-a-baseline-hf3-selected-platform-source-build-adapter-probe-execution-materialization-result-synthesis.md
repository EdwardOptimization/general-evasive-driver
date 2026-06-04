# M2629 Engineering Controller Route A Baseline HF3 Selected-Platform Source-Build Adapter-Probe Execution Materialization Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_selected_platform_source_build_adapter_probe_execution_attempt_design`
- manifest: `experiments/manifests/m2629-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-synthesis.json`
- parent audit: `docs/m2628-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-materialization-result-audit.md`
- parent summary: `runs/m2627_engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution/summary.json`
- route reference: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2630-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-design.json`
- next: `m2630-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-design`

## Route Decision

M2629 continues Route C high-fidelity interface preparation, but only to a
bounded execution-attempt design milestone. The accepted M2627/M2628 evidence
is sufficient to design a future selected-platform source-build/adapter-probe
execution-attempt protocol. It is not sufficient to claim dependency
readiness, source-build execution, adapter-probe execution, backend
availability, reset execution, reset success, rollout feasibility, validation
readiness, validation admission, validation result, high-fidelity readiness,
driver performance, paper evidence, finite-window-vs-GRU evidence,
current-sim verdict, or level3 self-identification.

This is consistent with `docs/post-m2470-route-plan.md`: current-sim remains a
diagnostic layer, Route A engineering-controller preparation may proceed, and
Route C may prepare the high-fidelity validation interface without waiting for
current-sim perfection. The same route plan also forbids another static loop
unless the artifact changes the next admission decision. M2630 is therefore
not another open-ended static artifact. It must design the bounded protocol for
a future actual execution attempt and define the stop condition that hands off
to M2631 materialization.

## Evidence Summary

M2627/M2628 accepted these bounded facts:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_selected_platform_source_build_adapter_probe_execution_design_materialization_preflight_pass
selected_platform_family: chrono_vehicle_or_equivalent_open_backend
selected_platform_source_build_adapter_probe_execution_design_materialized: true
source_build_command_contract_rows: 2/2 pass
adapter_probe_command_contract_rows: 2/2 pass
dependency_environment_isolation_guard_rows: 4/4 pass
source_build_artifact_capture_rows: 4/4 pass
adapter_probe_trace_capture_rows: 4/4 pass
outcome_taxonomy_rows: 10/10 pass
actor_action_guard_rows: 2/2 pass
claim_boundary_rows: 28/28 pass
materialization_gates: 13/13 pass
actor contract: P0 observation 72 action 3 [steer, throttle, brake]
```

M2627/M2628 also kept the execution and claim boundary false:

```text
external_install: false
external_import: false
runtime_execution: false
dependency_mutation: false
source_tree_mutation: false
network_access: false
source_build_executed: false
adapter_probe_executed: false
backend_started: false
reset_executed: false
environment_step_executed: false
policy_action_executed: false
rollout_executed: false
replay_executed: false
external_validation_execution: false
validation_protocol_ready: false
validation_admission_granted: false
validation_result_claim_allowed: false
backend_availability_claim_allowed: false
reset_success_claim_allowed: false
rollout_feasibility_claim_allowed: false
driver_performance_claim_allowed: false
```

The accepted evidence is a workflow and admission-control improvement. It
does not change closed-loop driver capability and does not change the paper
claim ladder. It reduces the risk that a future high-fidelity pilot route will
silently conflate command contracts with actual source-build/probe evidence.

## Supported Claims

Supported:

- M2627/M2628 accepted HF3 selected-platform source-build/adapter-probe
  execution design materialization evidence for
  `chrono_vehicle_or_equivalent_open_backend`.
- Source-build command contracts, adapter-probe command contracts,
  dependency/environment isolation guards, source-build artifact capture
  contracts, adapter-probe trace capture contracts, outcome taxonomy,
  actor/action guard, claim-boundary rows, and gate rows are present and pass.
- The P0 actor/action contract remains observation shape `72`, action shape
  `3`, and deployed action mapping `[steer, throttle, brake]`.
- No hidden/oracle actor input, diagnostic label, backend status, build/probe
  outcome, reset outcome, rollout outcome, validation outcome, selected
  platform, or protocol status was exposed to the actor.
- The next bounded step may design an execution-attempt protocol that tells a
  future materialization milestone exactly what command attempts, logs,
  traces, backend-discovery evidence, failure taxonomy, actor/action guards,
  claim-boundary checks, and gates must exist before any real execution route
  is interpreted.

## Falsified Or Rejected Claims

Not supported:

- dependency ready for execution
- source build executed
- adapter probe executed
- backend availability
- reset executed
- reset success
- environment step executed
- policy action executed
- rollout executed
- replay executed
- rollout feasibility
- validation protocol readiness
- validation admission
- validation readiness or validation result
- external validation execution
- high-fidelity validation readiness or result
- success rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2627/M2628 are static selected-platform source-build/adapter-probe execution
design materialization and audit. They do not build, probe, start a backend,
reset, step, run policy actions, roll out, replay, validate, compare
controller families, or prove professional driver behavior.

## Failure Taxonomy Summary

No accepted M2627/M2628 evidence indicates:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 validation-layer branch.
- `objective_overfit`: static design rows can still be overclaimed if treated
  as execution, readiness, validation, or performance evidence.
- `lineage_invalid`: not triggered here, but any future source-build or
  adapter-probe execution attempt needs explicit command logs, environment
  snapshots, trace capture, backend-discovery evidence, and claim-boundary
  audit evidence.

## Public-Gate Overfit Risk

Risk is medium-high. M2627/M2628 improve validation-preparation hygiene, but
they do not add driver capability evidence, paper-mechanism evidence, or
high-fidelity validation results. Continuing blindly would violate the
`post-m2470` hard stop against more static artifacts that cannot change an
admission decision.

The route remains worth one more bounded design step because the next
admission decision is not controller ranking. It is whether the selected
platform has a clean, auditable execution-attempt protocol that can later be
materialized without crossing dependency, backend, reset, validation, or actor
input boundaries.

## Next Branch Decision

Continue to:

```text
m2630-engineering-controller-route-a-baseline-hf3-selected-platform-source-build-adapter-probe-execution-attempt-design
```

M2630 must design the bounded actual execution-attempt protocol for a future
materializer. It should define:

- source-build execution command attempt/admission rows
- adapter-probe execution command attempt/admission rows
- dependency isolation and runtime guard rows
- execution-attempt log capture rows
- backend-discovery evidence capture rows
- execution failure taxonomy rows
- actor/action guard rows
- claim-boundary rows
- gate matrix

M2630 must not install dependencies, import high-fidelity packages, mutate
source trees, use network dependency resolution, run source builds, run
adapter probes, start a backend, reset, step, execute policy action, roll out,
replay, validate, train, rank, compute success rates, select winners, promote
checkpoints, or claim dependency readiness, backend availability, validation
readiness, validation result, driver performance, paper evidence,
finite-window-vs-GRU evidence, current-sim verdict, high-fidelity result, or
self-ID.

The next handoff after M2630 should be M2631 execution-attempt materialization
preflight. M2631 may materialize attempt contracts and capture schemas, but
the actual external execution boundary must still remain explicit and audited
before any result is interpreted.
