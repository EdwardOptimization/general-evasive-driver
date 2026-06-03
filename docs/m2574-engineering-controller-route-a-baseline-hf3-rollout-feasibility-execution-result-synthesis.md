# M2574 Engineering Controller Route A Baseline HF3 Rollout-Feasibility Execution Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_validation_readiness_boundary_design`
- manifest: `experiments/manifests/m2574-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-result-synthesis.json`
- parent audit: `docs/m2573-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-materialization-result-audit.md`
- parent materialization summary: `runs/m2572_engineering_controller_route_a_hf3_rollout_feasibility_execution/summary.json`
- follow-up manifest: `experiments/manifests/m2575-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-design.json`
- next: `m2575-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-design`

## Evidence Summary

M2572/M2573 provide accepted HF3 rollout-feasibility execution evidence:

```text
rollout request rows: 2/2 pass
fixed policy source rows: 1/1 pass
rollout plan rows: 2/2 pass
policy-action audit rows: 16/16 pass
backend step/outcome rows: 16/16 pass
actor-view contract rows: 18/18 pass
claim-boundary checks: 9/9 pass
materialization gates: 10/10 pass
candidate roles: stable avoidable/AEB-feasible, stable AES/AEB-infeasible
fixed policy source: M1154 public-base alpha_0_05
target horizon: 8 steps/request
step counts: 8 per rollout request
backend statuses: running=16
terminated/truncated: 0/0
actor contract: P0 observation 72 / action 3
policy action executed: true
environment step executed: true
repo-local rollout-feasibility execution observed: true
rollout success claim allowed: false
validation claim allowed: false
success-rate/ranking/promotion/driver-performance verdict: false
```

This is enough to design a bounded validation-readiness boundary. It is not
enough to claim rollout success, high-fidelity validation readiness, validation
result, driver performance, controller ranking, paper evidence, or self-ID.

## Supported Claims

Supported:

- Route A HF3 reset/action/step feasibility execution is internally consistent
- exactly two HF3 candidates were represented
- a single fixed M1154 policy source was used
- the M1154 policy source was not ranked, compared, or promoted
- both candidates completed eight repo-local policy-action/backend-step rows
- every completed step preserved actor-view availability
- P0 `72/3` actor/action contract remains unchanged
- diagnostics, taxonomy labels, backend statuses, reset outcomes, and rollout
  outcomes remained outside actor-visible inputs
- no external high-fidelity simulator was installed, imported, or run
- the next bounded step should design validation-readiness boundary artifacts,
  not execute validation

## Falsified Claims

Not supported, and explicitly rejected:

- pilot admission
- rollout success
- high-fidelity validation readiness or validation result
- external simulator behavior transfer
- success-rate or controller-family verdict
- controller ranking or winner selection
- checkpoint promotion
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2572/M2573 are a short repo-local feasibility smoke. They do not measure
scenario success, external dynamics transfer, or professional-driver behavior.

## Failure Taxonomy Summary

No accepted M2572/M2573 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved outside this HF3 feasibility route.
- `objective_overfit`: short-horizon repo-local rows can be overclaimed if
  treated as rollout success, validation readiness, or benchmark evidence.
- `scenario_sampling_failure`: not triggered here, but the current evidence
  covers only two HF3 route roles and eight steps per role.

## Public Gate Overfit Risk

Risk is medium. M2572 is the first action/step evidence after reset-only work,
but it is still repo-local and short horizon. Treating it as a validation
result would overstate the evidence.

The next step must therefore design validation-readiness boundary artifacts
that:

- separate readiness checks from validation execution
- preserve the P0 `72/3` actor/action contract
- define platform and dependency boundaries without installing or importing an
  external simulator
- define which Route C HF4 discrepancy questions can be asked only after
  external validation exists
- keep labels, feasibility classes, diagnostics, backend statuses, reset
  outcomes, rollout outcomes, and validation outcomes out of actor inputs
- keep ranking, promotion, success-rate, driver-performance, paper,
  FW-vs-GRU, current-sim verdict, high-fidelity validation result, and self-ID
  claims out of scope

## Next Branch Decision

Continue to:

```text
m2575-engineering-controller-route-a-baseline-hf3-validation-readiness-boundary-design
```

M2575 should design the boundary artifacts required before any validation
execution is meaningful. It should define:

- validation-readiness request rows for the two accepted HF3 candidates
- evidence admission rows binding M2572/M2573 feasibility evidence to a
  readiness-design input, not a validation result
- platform boundary rows separating repo-local adapter evidence from external
  high-fidelity execution
- dependency/install/import policy rows
- scenario-discrepancy question rows for the later HF4 report
- actor-input isolation rows
- claim-boundary rows separating readiness design from validation result,
  driver performance, ranking, and self-ID
- an M2576 validation-readiness materialization gate matrix

M2575 must not install, import, or run external simulation, execute new policy
actions, step environments, run validation, compute success rates, rank
controllers, promote checkpoints, or make driver-performance claims.
