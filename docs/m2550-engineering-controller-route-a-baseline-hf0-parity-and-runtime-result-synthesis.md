# M2550 Engineering Controller Route A Baseline HF0 Parity And Runtime Result Synthesis

- status: completed
- synthesis decision: `continue_to_hf1_p0_parity_smoke_design`
- manifest: `experiments/manifests/m2550-engineering-controller-route-a-baseline-hf0-parity-and-runtime-result-synthesis.json`
- parent audit: `docs/m2549-engineering-controller-route-a-baseline-hf0-parity-and-runtime-materialization-result-audit.md`
- parent materialization summary: `runs/m2548_engineering_controller_route_a_hf0_parity_and_runtime_materialization/summary.json`
- follow-up manifest: `experiments/manifests/m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design.json`
- next: `m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design`

## Evidence Summary

M2548/M2549 provide accepted source-level HF0 readiness evidence:

```text
HF0 P0 parity checks: 5/5 pass
action mapping checks: 7/7 pass
runtime schema fields: 21
actor inference cost rows: 270
materialization gates: 8/8 pass
policy checkpoints admitted: 3/3
actor contract: P0 observation 72 / action 3
external high-fidelity simulation: not installed/imported/run
```

This is real interface/readiness progress. It proves that the Route A
baseline has materialized P0 parity, action-mapping, and per-checkpoint
actor-forward runtime artifacts. It does not prove high-fidelity validation
or driver performance.

## Supported Claims

Supported:

- the Route A source-level HF0 P0 parity/runtime materialization is complete
- all three diagnostic Route A policy checkpoints remain admissible under P0 `72/3`
- actor-forward runtime rows are denominator-complete for the specified batch and iteration matrix
- action mapping preserves deployed `[steer, throttle, brake]` semantics
- diagnostics-only keys remain outside actor-visible observations
- the branch is ready to design a bounded HF1 P0 parity smoke materialization

## Falsified Claims

Not supported, and explicitly rejected:

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

The M2537 mitigation-proof limitation also remains unresolved. M2548/M2549
do not repair behavior, run closed-loop policy rollouts, or evaluate
scenario success.

## Failure Taxonomy Summary

No M2548/M2549 failure is accepted for:

- `contract_violation`
- `lineage_invalid`
- `metric_artifact`
- `scenario_sampling_failure`

Open limitations:

- `behavior_regression`: the earlier mitigation-primary proof issue remains unresolved.
- `proof_washout`: the M2532/M2537 repair lineage still lacks full protected proof success.
- `objective_overfit`: runtime/parity evidence must not be converted into policy ranking or protected-row tuning.

## Public Gate Overfit Risk

Risk is medium-low for the HF0 parity/runtime artifacts themselves: the
checks are contract and artifact gates, not public behavior rows. Risk rises
if runtime rows are used to rank policies or if source-level parity is
misrepresented as high-fidelity validation.

The next step should therefore remain bounded: design HF1 P0 parity smoke
artifacts and gates, while keeping validation, ranking, and driver-performance
claims out of scope.

## Next Branch Decision

Continue to:

```text
m2551-engineering-controller-route-a-baseline-hf1-p0-parity-smoke-design
```

M2551 should design the HF1 P0 parity smoke materialization. It should define:

- candidate external-backend adapter boundary checks without installing or running the external backend
- required actor-visible field parity rows
- P0 observation shape/value-range parity checks
- deployed action mapping parity checks
- hidden/oracle diagnostics exclusion gates
- M2552 materialization artifacts and pass/fail gates

M2551 must not run external high-fidelity simulation, execute policy rollouts,
train, rank, promote, compute success rates, or claim validation.
