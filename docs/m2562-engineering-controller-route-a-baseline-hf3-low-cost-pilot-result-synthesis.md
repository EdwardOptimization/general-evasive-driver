# M2562 Engineering Controller Route A Baseline HF3 Low-Cost Pilot Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_reset_feasibility_execution_design`
- manifest: `experiments/manifests/m2562-engineering-controller-route-a-baseline-hf3-low-cost-pilot-result-synthesis.json`
- parent audit: `docs/m2561-engineering-controller-route-a-baseline-hf3-low-cost-pilot-materialization-result-audit.md`
- parent materialization summary: `runs/m2560_engineering_controller_route_a_hf3_low_cost_pilot_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2563-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-design.json`
- next: `m2563-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-design`

## Evidence Summary

M2560/M2561 provide accepted source-level HF3 low-cost pilot preflight
evidence:

```text
pilot candidate rows: 2/2 pass
reset-feasibility plan rows: 2/2 pass
rollout-feasibility plan rows: 2/2 pass
external-boundary checks: 6/6 pass
claim-boundary checks: 7/7 pass
materialization gates: 8/8 pass
candidate roles: stable avoidable/AEB-feasible, stable AES/AEB-infeasible
candidate admission status: requires_m2560_reset_and_rollout_feasibility=2
source binding counts: baseline_reference_binding=1, materialization_candidate_binding=1
actor contract: P0 observation 72 / action 3
pilot admission: false
policy action allowed/executed: false
reset/step/rollout execution: false
external simulator install/import/run: false
validation/ranking/driver-performance verdict: false
```

This is enough to design a bounded reset-feasibility execution milestone. It
is not enough to execute a reset, admit a pilot, claim reset success, claim
rollout success, claim validation readiness, or rank controller families.

## Supported Claims

Supported:

- the Route A HF3 low-cost pilot preflight is internally consistent
- exactly two pilot candidates are represented
- stable avoidable/AEB-feasible and stable AES/AEB-infeasible are the only
  current pilot candidates
- reset-feasibility and rollout-feasibility plans exist for both candidates
- external backend boundary checks and claim-boundary checks are complete
- P0 `72/3` actor/action contract remains unchanged
- the next bounded step should design a reset-feasibility execution milestone
  with explicit backend availability, reset request, reset outcome, and claim
  boundary artifacts

## Falsified Claims

Not supported, and explicitly rejected:

- pilot admission
- reset success
- rollout success
- high-fidelity validation readiness or result
- external simulator behavior transfer
- controller ranking or winner selection
- checkpoint promotion
- success-rate or controller-family verdict
- driver-performance claim
- current-sim verdict
- paper-level evidence
- finite-window-vs-GRU result
- level3 self-identification evidence

M2560/M2561 only define and audit preflight rows. They do not execute the
vehicle backend or measure closed-loop behavior.

## Failure Taxonomy Summary

No accepted M2560/M2561 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved and are outside the HF3 preflight route.
- `objective_overfit`: preflight rows can be overclaimed if the next step
  turns candidate status into pilot admission without measured reset evidence.
- `scenario_sampling_failure`: not triggered yet, but reset execution design
  must separate backend availability, reset request validity, and reset
  outcome recording before rollout planning.

## Public Gate Overfit Risk

Risk is medium. The accepted rows are process and artifact gates, not public
behavior rows. The risk is that they become a substitute for measured reset
feasibility.

The next step must therefore design reset-feasibility execution artifacts that:

- keep candidate labels and feasibility statuses metadata-only
- require backend availability to be recorded explicitly
- define reset requests without changing actor input or action contract
- record reset outcomes without claiming rollout success or validation
- keep controller ranking, driver performance, paper, FW-vs-GRU, current-sim,
  high-fidelity validation, and self-ID claims out of scope

## Next Branch Decision

Continue to:

```text
m2563-engineering-controller-route-a-baseline-hf3-reset-feasibility-execution-design
```

M2563 should design a bounded reset-feasibility execution materialization. It
should define:

- reset-execution candidate rows for the two HF3 pilot candidates
- backend availability and no-install/no-dependency-mutation checks
- reset request contract rows
- reset execution plan rows
- reset outcome schema rows
- claim-boundary rows separating reset feasibility from rollout feasibility,
  validation, ranking, and driver performance
- an M2564 materialization gate matrix

M2563 must not install/import/run external high-fidelity simulation, execute
policy actions, step environments, train, rank, promote, compute success
rates, or claim validation.
