# M2570 Engineering Controller Route A Baseline HF3 Measured Reset-Feasibility Execution Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf3_rollout_feasibility_execution_design`
- manifest: `experiments/manifests/m2570-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-result-synthesis.json`
- parent audit: `docs/m2569-engineering-controller-route-a-baseline-hf3-measured-reset-feasibility-execution-materialization-result-audit.md`
- parent materialization summary: `runs/m2568_engineering_controller_route_a_hf3_measured_reset_feasibility_execution/summary.json`
- follow-up manifest: `experiments/manifests/m2571-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-design.json`
- next: `m2571-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-design`

## Evidence Summary

M2568/M2569 provide accepted HF3 reset-only execution evidence:

```text
measured reset request rows: 2/2 pass
backend probe rows: 2/2 pass
reset-only execution rows: 2/2 pass
actor-view contract rows: 2/2 pass
reset outcome rows: 2/2 pass
claim-boundary checks: 8/8 pass
materialization gates: 9/9 pass
candidate roles: stable avoidable/AEB-feasible, stable AES/AEB-infeasible
reset execution status: reset_observed_actor_view_available=2
actor contract: P0 observation 72 / action 3
reset-only execution observed: true
reset execution attempted count: 2
actor-view available count: 2
policy action executed: false
environment step executed: false
rollout executed: false
reset success claim allowed: false
validation/ranking/driver-performance verdict: false
```

This is enough to design a bounded rollout-feasibility execution milestone.
It is not enough to claim reset success, rollout success, validation readiness,
driver performance, or controller-family ranking.

## Supported Claims

Supported:

- the Route A HF3 reset-only execution layer is internally consistent
- exactly two reset candidates reached repo-local backend reset
- both reset candidates produced actor views after reset
- P0 `72/3` actor/action contract remains unchanged after reset
- no policy action, step, rollout, training, ranking, or validation was run
- the next bounded step should design rollout-feasibility execution with a
  fixed RL checkpoint policy source, short-horizon policy action rows,
  step/outcome rows, actor-contract checks, and claim-boundary gates

## Falsified Claims

Not supported, and explicitly rejected:

- pilot admission
- reset success
- rollout feasibility or rollout success
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

M2568/M2569 only execute reset. They do not execute policy actions, step the
environment, or measure closed-loop behavior.

## Failure Taxonomy Summary

No accepted M2568/M2569 failure:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: earlier mitigation-primary proof failures remain
  unresolved and are outside this reset-only route.
- `objective_overfit`: reset-only rows can be overclaimed if treated as
  rollout feasibility or validation evidence.
- `scenario_sampling_failure`: not triggered yet, but rollout feasibility must
  define horizon, action policy, step outcomes, and failure taxonomy before any
  interpretation.

## Public Gate Overfit Risk

Risk is medium. Reset-only evidence is a necessary execution boundary but is
not behavior evidence. The overfit risk is turning a successful reset into a
success-rate or driver-performance claim.

The next step must therefore design rollout-feasibility artifacts that:

- use a fixed, predeclared RL checkpoint policy source
- preserve the P0 `72/3` actor/action contract
- record policy actions and backend steps as audit evidence
- keep labels, feasibility classes, diagnostics, and outcomes out of actor
  inputs
- use a small horizon sufficient for feasibility smoke evidence, not a
  performance verdict
- keep ranking, promotion, validation, paper, FW-vs-GRU, current-sim verdict,
  high-fidelity validation, and self-ID claims out of scope

## Next Branch Decision

Continue to:

```text
m2571-engineering-controller-route-a-baseline-hf3-rollout-feasibility-execution-design
```

M2571 should design a bounded rollout-feasibility execution materialization.
It should define:

- rollout request rows for the two HF3 reset candidates
- fixed policy source rows using the promoted M1154 public-base checkpoint
- rollout execution plan rows with a short horizon and no ranking or promotion
- policy action audit rows preserving `[steer, throttle, brake]`
- backend step/outcome rows recording step count, termination/truncation, and
  actor-view availability
- claim-boundary rows separating rollout feasibility from rollout success,
  validation, ranking, and driver performance
- an M2572 rollout-feasibility materialization gate matrix

M2571 must not run policy actions or rollouts itself. M2572 may run the bounded
repo-local rollout only if it writes the designed artifacts and keeps all
validation and driver-performance claims false.
