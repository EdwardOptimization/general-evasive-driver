# M2617 Engineering Controller Route A Baseline HF3 Selected-Platform Executable-Protocol Readiness Materialization Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_selected_platform_reset_feasibility_readiness_design`
- manifest: `experiments/manifests/m2617-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-synthesis.json`
- parent audit: `docs/m2616-engineering-controller-route-a-baseline-hf3-selected-platform-executable-protocol-readiness-materialization-result-audit.md`
- parent materialization summary: `runs/m2615_engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness/summary.json`
- follow-up manifest: `experiments/manifests/m2618-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-design.json`
- next: `m2618-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-design`

## Evidence Summary

M2615/M2616 provide accepted HF3 selected-platform executable-protocol
readiness materialization evidence:

```text
status_pass: true
result_class: engineering_controller_route_a_hf3_selected_platform_executable_protocol_readiness_materialization_preflight_pass
source/dependency review rows: 4/4 pass
build/probe plan rows: 4/4 pass
reset/step API readiness rows: 2/2 pass
actor extractor parity rows: 2/2 pass
action mapping parity rows: 2/2 pass
scenario-role binding rows: 2/2 pass
result export/replay readiness rows: 3/3 pass
validation-admission prerequisite rows: 2/2 pass
actor/action guard rows: 2/2 pass
claim-boundary checks: 28/28 pass
materialization gates: 14/14 pass
selected_platform_family_in_m2615: chrono_vehicle_or_equivalent_open_backend
selected_platform_executable_protocol_readiness_design_materialized_in_m2615: true
external_install_allowed_in_m2615: false
external_import_allowed_in_m2615: false
runtime_execution_allowed_in_m2615: false
dependency_mutation_allowed_in_m2615: false
source_build_executed_in_m2615: false
adapter_probe_executed_in_m2615: false
reset_executed_in_m2615: false
environment_step_executed_in_m2615: false
policy_action_executed_in_m2615: false
rollout_executed_in_m2615: false
replay_executed_in_m2615: false
external_validation_execution_allowed_in_m2615: false
validation_protocol_ready_in_m2615: false
validation_admission_granted_in_m2615: false
validation_result_claim_allowed: false
driver_performance_claim_allowed_in_m2615: false
actor contract: P0 observation 72 / action 3
```

This is sufficient to continue from selected-platform executable-protocol
readiness bookkeeping to a bounded reset-feasibility readiness design. It is
not sufficient to declare dependency execution readiness, source-build
execution, adapter-probe execution, reset feasibility, rollout feasibility,
validation protocol readiness, validation admission, validation result, HF4
discrepancy answers, controller ranking, driver performance, paper evidence,
finite-window-vs-GRU evidence, current-sim verdict, high-fidelity validation
result, or level3 self-identification.

## Supported Claims

Supported:

- HF3 selected-platform executable-protocol readiness materialization artifacts
  are present and audited
- the selected platform family remains
  `chrono_vehicle_or_equivalent_open_backend`
- source/dependency review admission rows are materialized as static
  prerequisites for later execution decisions
- build/probe plan rows are materialized while source build and adapter probe
  remain future prerequisites
- reset/step API readiness rows describe static contracts only
- actor extractor parity rows preserve deployable P0 actor-visible inputs
- action mapping parity rows preserve the deployed `[steer, throttle, brake]`
  action contract
- scenario-role rows keep stable avoidable/AEB-feasible and stable
  AES/AEB-infeasible pilot role metadata outside actor-visible input
- result export/replay rows are static contracts only
- validation-admission prerequisite rows keep reset feasibility, rollout
  feasibility, executable protocol, source build/adapter probe, and
  holdout/generalization policy as future prerequisites
- actor/action guard rows preserve P0 `72/3`
- the next bounded step may design selected-platform reset-feasibility
  readiness artifacts while still forbidding execution, validation, ranking,
  paper, finite-window-vs-GRU, current-sim, high-fidelity verdict, self-ID, and
  driver-performance claims

## Falsified Claims

Not supported, and explicitly rejected:

- dependency ready for execution
- source build executed
- adapter probe executed
- reset executed
- environment step executed
- policy action executed
- rollout executed
- replay executed
- validation protocol ready
- validation admission granted
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

M2615/M2616/M2617 are selected-platform executable-protocol readiness
materialization, audit, and synthesis only. They do not install, import, build,
probe, reset, step, run a policy action, roll out, replay, validate, compare
controller families, or prove professional driver behavior.

## Failure Taxonomy Summary

No accepted M2615/M2616 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 validation-layer route.
- `objective_overfit`: executable-protocol rows can be overclaimed if treated
  as dependency execution readiness, reset feasibility, validation protocol
  readiness, validation admission, validation readiness, validation result, or
  performance evidence.
- `lineage_invalid`: not triggered here, but future validation readiness still
  requires reset-feasibility evidence, rollout-feasibility evidence,
  source-build or adapter-probe execution evidence, validation-admission
  evidence, explicit validation execution evidence, and claim-boundary audit
  evidence.

Current evidence is infrastructure and process evidence. It is not a driver
ability measurement.

## Public Gate Overfit Risk

Risk remains high to medium-high. M2615-M2617 are validation-layer process
steps and do not add new closed-loop driver behavior, a new controller-family
comparison, a current-sim verdict, self-ID evidence, or high-fidelity execution
evidence.

The branch does improve validation-layer state: selected-platform source
review, build/probe planning, reset/step API contracts, actor extractor parity,
action mapping parity, scenario-role binding, result export/replay readiness,
validation-admission prerequisites, actor/action guard, claim-boundary rows,
and gate rows are materialized and audited. That reduces overclaim risk before
reset-feasibility readiness design, but it does not move the driver capability
or paper verdict.

The paper-governing route remains unchanged. Self-identification and GRU
advantage are still hypotheses, not default truths. High-fidelity simulation is
a validation layer after the current-sim verdict and controller set are frozen;
it is not self-ID proof by itself. Source-singleton positives and reset-only
evidence remain insufficient for level3 self-identification. M2617 therefore
adds validation-preparation clarity only and creates no paper verdict delta.

## Next Branch Decision

Continue to:

```text
m2618-engineering-controller-route-a-baseline-hf3-selected-platform-reset-feasibility-readiness-design
```

M2618 should design bounded selected-platform reset-feasibility readiness
artifacts. It should define:

- reset request schema rows
- initial-state admission rows
- actor-view parity rows
- deterministic seed and lineage rows
- reset outcome taxonomy guard rows
- reset-execution precondition rows
- actor/action guard rows preserving P0 `72/3`
- claim-boundary rows and a materialization gate matrix for M2619

M2618 is a design-only step. It must not install/import/run external
simulation, execute source build, execute adapter probe, execute reset, execute
policy actions, step environments, roll out, replay, run validation, train,
rank controllers, promote checkpoints, compute success rates, or make
driver-performance, paper, finite-window-vs-GRU, current-sim, high-fidelity
validation, or self-ID claims.
