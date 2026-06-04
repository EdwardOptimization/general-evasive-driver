# M2613 Engineering Controller Route A Baseline HF3 Selected-Platform Dependency/Protocol Readiness Materialization Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_selected_platform_executable_protocol_readiness_design`
- manifest: `experiments/manifests/m2613-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-synthesis.json`
- parent audit: `docs/m2612-engineering-controller-route-a-baseline-hf3-selected-platform-dependency-protocol-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2611_engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2614-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-design.json`
- next: `m2614-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-design`

## Evidence Summary

M2611/M2612 provide accepted HF3 selected-platform dependency/protocol
readiness materialization evidence:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_selected_platform_dependency_protocol_readiness_materialization_preflight_pass
dependency inventory rows: 4/4 pass
source/build/adapter probe readiness rows: 4/4 pass
protocol skeleton rows: 2/2 pass
validation-admission prerequisite rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary checks: 20/20 pass
materialization gates: 12/12 pass
selected_platform_family_in_m2611: chrono_vehicle_or_equivalent_open_backend
external_install_allowed_in_m2611: false
external_import_allowed_in_m2611: false
runtime_execution_allowed_in_m2611: false
dependency_mutation_allowed_in_m2611: false
source_build_executed_in_m2611: false
adapter_probe_executed_in_m2611: false
reset_allowed_in_m2611: false
policy_action_allowed_in_m2611: false
environment_step_allowed_in_m2611: false
rollout_allowed_in_m2611: false
external_validation_execution_allowed_in_m2611: false
validation_protocol_ready_in_m2611: false
validation_admission_granted_in_m2611: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2611: false
actor contract: P0 observation 72 / action 3
```

This is enough to continue from selected-platform dependency/protocol
readiness bookkeeping to a bounded executable-protocol readiness design. It is
not enough to declare dependency execution readiness, run a source build, run
an adapter probe, execute reset/step/rollout/validation, claim high-fidelity
validation readiness, report an external validation result, answer HF4
discrepancy questions, rank controllers, or claim driver performance.

## Supported Claims

Supported:

- Route A HF3 selected-platform dependency/protocol readiness materialization
  artifacts are present and audited
- the selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- dependency inventory rows are materialized for vehicle dynamics source,
  scenario adapter, sensor/actor interface, and result export/replay contracts
- source/build/adapter probe readiness rows are static contracts only
- protocol skeleton rows are materialized for stable avoidable/AEB-feasible
  and stable AES/AEB-infeasible HF3 pilot roles
- validation-admission prerequisite rows keep reset feasibility, rollout
  feasibility, executable protocol, source build/adapter probe, and
  holdout/generalization policy as future prerequisites
- actor/action guard rows preserve P0 `72/3`
- hidden/oracle input, diagnostics, taxonomy labels, backend status, reset
  outcome, rollout outcome, validation outcome, platform selection,
  platform-selection criteria, platform-selection decision, selected platform,
  and protocol status remain outside actor-visible inputs
- the next bounded step may design selected-platform executable-protocol
  readiness artifacts while still forbidding dependency mutation, source build,
  adapter probe, reset/step/rollout/validation execution, validation
  readiness/result, ranking, and driver-performance claims

## Falsified Claims

Not supported, and explicitly rejected:

- dependency ready for execution
- source build or adapter probe executed
- validation protocol readiness
- validation admission
- external validation execution
- high-fidelity validation readiness
- high-fidelity validation result
- HF4 discrepancy result
- rollout success
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2611/M2612/M2613 are selected-platform dependency/protocol readiness
materialization, audit, and synthesis only. They do not install, import, build,
probe, or run a high-fidelity simulator, complete an executable validation
protocol, measure scenario success, compare controller families, or prove
professional driver behavior.

## Failure Taxonomy Summary

No accepted M2611/M2612 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 validation-layer route.
- `objective_overfit`: selected-platform dependency/protocol readiness rows
  can be overclaimed if treated as dependency execution readiness, validation
  protocol readiness, validation admission, validation readiness, validation
  result, or performance evidence.
- `lineage_invalid`: not triggered here, but future validation readiness still
  requires executable-protocol readiness design, materialization, audit,
  explicit validation-admission evidence, explicit execution evidence, and
  claim-boundary audit evidence.

## Public Gate Overfit Risk

Risk remains high. M2611-M2613 are validation-layer process steps. They do not
add new closed-loop driver behavior, new controller-family comparison, new
self-ID proof, or new high-fidelity execution evidence.

The branch does change validation-layer evidence state: the selected platform
family has an audited dependency inventory, static probe-readiness contract,
protocol skeleton, and validation-admission prerequisite panel. That reduces
ambiguity before executable protocol readiness can be designed, but it does
not move the driver capability or paper verdict.

This milestone is the required branch synthesis after the recent cadence of
infrastructure milestones. The next step should not be another
dependency/protocol readiness materialization artifact. It should either move
to a concrete executable-protocol readiness design, repair a specific artifact
gap, pivot, or stop. Continuing is justified only because Route C requires an
executable protocol boundary before any reset feasibility or external
validation execution can be proposed.

## Next Branch Decision

Continue to:

```text
m2614-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-design
```

M2614 should design bounded selected-platform executable-protocol readiness
artifacts. It should define:

- source/equivalent trace and dependency review admission contract
- build/probe plan rows without executing source build or adapter probe
- reset/step API readiness rows without reset or environment stepping
- P0 actor observation extractor parity rows without actor-visible metadata
- deployed `[steer, throttle, brake]` action mapping parity rows
- scenario-role binding rows for stable avoidable/AEB-feasible and stable
  AES/AEB-infeasible pilots
- deterministic result export/replay readiness rows
- validation-admission prerequisite rows keeping validation protocol readiness,
  validation admission, execution, result, and performance claims false
- actor/action guard rows preserving P0 `72/3`
- claim-boundary rows and a materialization gate matrix for M2615

M2614 may design the bounded executable-protocol readiness artifacts if all
guards remain explicit. It must not install/import/run external simulation,
execute source build, execute adapter probe, execute resets, execute policy
actions, step environments, run validation, compute success rates, rank
controllers, promote checkpoints, or make driver-performance claims.
