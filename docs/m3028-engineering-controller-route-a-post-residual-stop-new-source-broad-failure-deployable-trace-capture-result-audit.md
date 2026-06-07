# M3028 Engineering Controller Route A Post-Residual-Stop New Source Broad-Failure Deployable Trace Capture Result Audit

## Metadata

- status: completed
- decision: `accept_m3027_claim_safe_raw_trace_capture_route_to_m3029_target_source_feasibility_materialization_preflight`
- manifest: `experiments/manifests/m3028-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-deployable-trace-capture-result-audit.json`
- audited summary: `runs/m3027_engineering_controller_route_a_post_residual_stop_new_source_broad_failure_deployable_trace_capture_preflight/summary.json`
- audited doc: `docs/m3027-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-deployable-trace-capture-preflight.md`
- follow-up manifest: `experiments/manifests/m3029-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-materialization-preflight.json`
- next: `m3029-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-materialization-preflight`

## Audit Decision

M3028 accepts M3027 as a complete and claim-safe raw deployable trace-capture
preflight.

Formal decision:

```text
accept_m3027_claim_safe_raw_trace_capture_route_to_m3029_target_source_feasibility_materialization_preflight
```

The accepted result is raw actor-view trace availability only. M3027 clears the
M3025/M3026 raw-trace blocker for the preserved 32-row denominator, but it does
not by itself establish target-source feasibility, numeric target tensors,
local-action search readiness, residual fitting readiness, validation
readiness, repair success, or any driver-performance claim.

The next legal route is a bounded target-source feasibility materialization
preflight that joins the M3027 raw trace index with the M3025 readiness rows.
It is not target tensor materialization, local-action search, fitting, training,
validation, ranking, promotion, or a paper-route claim.

## M3027 Result

M3027 passes artifact and claim-boundary checks:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
capture plan rows: 32
raw trace index rows: 32
raw trace files on disk: 32
future target raw traces: 29
success identity raw traces: 3
raw trace availability rows: 32
raw trace guard rows: 32
actor contract guard rows: 19
claim boundary rows: 18
gate rows: 18
failed gates: 0
```

The raw trace index preserves the intended denominator:

```text
future_target_candidate rows: 29
success_identity_guard rows: 3
```

Every indexed raw trace file exists and loads successfully. The captured step
range is:

```text
trace step count min: 31
trace step count max: 177
```

## Raw Trace Audit

M3027 persists actor-view tensors for all 32 executed rows:

```text
observation_trace: T x 72
action_trace: T x 3
next_observation_trace: T x 72
reward_trace: T
done_trace: T
timeout_trace: T
raw trace tensors finite: true
actor observation/action: 72/action 3
checkpoint loaded read-only: true
checkpoint mutated/promoted: false
direct profile policy mode: true
```

The tensor files use the deployed actor-view trace schema:

```text
observation_trace
action_trace
next_observation_trace
reward_trace
done_trace
timeout_trace
```

This is a data-availability improvement only. The traces still do not define a
numeric target tensor, teacher action, target delta, mask, loss, fitting
contract, validation denominator, ranking rule, promotion rule, or performance
verdict.

## Actor And Guardrail Audit

M3027 preserves the actor contract:

```text
actor observation/action: 72/action 3
actor input contract changed: false
hidden/oracle actor input detected: false
future target actor input required: false
source labels actor-visible: false
route labels actor-visible: false
outcome labels actor-visible: false
objective labels actor-visible: false
readiness labels actor-visible: false
success/progress labels actor-visible: false
verdict labels actor-visible: false
TTC actor input required: false
```

All source ids, row roles, objective families, failure families, readiness
labels, target provenance, outcomes, completion reasons, and feasibility
labels remain trainer/evaluator metadata only. They are not actor inputs.

The three success identity rows remain guard rows. They are not positive future
target candidates and do not establish a repair target.

## Supported Claims

M3028 supports only:

```text
M3027 captured complete raw deployable actor-view traces for 29 future target candidates and 3 success identity guards.
M3027 preserved the M3025 readiness denominator and actor 72/action 3 contract.
M3027 wrote finite observation/action/next-observation/reward traces and bool done/timeout traces.
M3027 loaded checkpoints read-only and did not mutate, rank, select, or promote checkpoints.
M3027 did not run local-action search, materialize numeric targets, fit, train, validate, rank, promote, or claim repair success or performance.
The next admissible step is target-source feasibility materialization using M3025 readiness rows plus M3027 raw trace rows.
```

These are artifact completeness, data availability, row accounting, and
boundary claims only.

## Rejected Claims

M3028 rejects:

```text
M3027 established target-source feasibility: false
M3027 materialized numeric target tensors: false
M3027 ran local-action search: false
M3027 established fitting readiness: false
M3027 fitted, trained, validated, ranked, selected, or promoted a residual head: false
M3027 changed actor inputs or action contract: false
M3027 proved repair success or driver performance: false
M3027 produced paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence: false
```

## Next Route

M3028 selects exactly one next route:

```text
m3029-engineering-controller-route-a-post-residual-stop-new-source-broad-failure-target-source-feasibility-materialization-preflight
```

M3029 must be a bounded target-source feasibility materialization preflight. It
must join:

```text
M3025 target-source readiness rows
M3025 success identity guard rows
M3027 raw trace index rows
M3027 raw trace availability rows
M3027 raw trace guard rows
```

The required accounting is:

```text
future target candidate rows: 29
success identity guard rows: 3
total denominator rows: 32
```

M3029 may materialize trainer/evaluator-side feasibility rows only. It must
keep target labels, source labels, row roles, outcomes, objective families,
feasibility status, and provenance actor-invisible. It must not materialize
numeric target tensors, run local-action search, fit, train, validate, rank,
select, promote, mutate checkpoints, tune profiles, or claim repair success,
driver performance, paper evidence, current-sim verdict, high-fidelity
evidence, finite-window-vs-GRU evidence, full-driver completion, or self-ID
evidence.
