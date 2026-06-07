# M2975 Engineering Controller Route A Actor-Head Delta Nonzero Residual Training Trace Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2976_deployable_trace_capture_design`
- manifest: `experiments/manifests/m2975-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-branch-synthesis.json`
- synthesis artifact: `docs/m2975-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-branch-synthesis.md`
- parent audit: `docs/m2974-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-training-trace-panel-result-audit.md`
- parent summary: `runs/m2973_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_training_trace_panel_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2976-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-design.json`
- next: `m2976-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-deployable-trace-capture-design`

M2975 synthesizes the M2969-M2974 nonzero residual training-admission and
trace-readiness branch. The branch reached a useful negative readiness result:
the candidate/guard accounting is complete and claim-safe, but raw deployable
observation/action traces are not persisted, so residual fitting is still
blocked.

## Synthesis Questions

### evidence_summary

The accepted evidence chain is:

```text
M2969: designed one guarded nonzero residual training-admission route.
M2970: materialized the training-admission surface over 43 non-success candidates, 13 success identity guards, and 11 stale guardrails.
M2971: accepted M2970 as complete and claim-safe.
M2972: required trace availability before any residual fitting.
M2973: materialized trace source, training panel, guard, availability, actor, claim, and gate artifacts.
M2974: accepted M2973 as complete and claim-safe, but rejected residual fitting readiness.
```

The accepted M2973/M2974 accounting is:

```text
status_pass: true
gate_matrix_pass: true
training trace panel rows: 43
trace guard rows: 24
trace availability rows: 67
trace metadata present rows: 56
raw trace persisted rows: 0
trace panel ready for residual fitting: false
success identity guard rows: 13
stale guardrail rows: 11
actor observation/action: 72/action 3
```

The diagnostic outcome taxonomy remains inherited from M2960:

```text
diagnostic_success: 13
off_track: 35
collision: 7
speed_too_low: 1
non_success: 43
```

The route-plan constraint from `docs/post-m2470-route-plan.md` remains active:
do not let static current-sim infrastructure become the main loop, and do not
treat process artifacts as driver-performance, paper, current-sim,
high-fidelity, finite-window-vs-GRU, full-driver, or self-ID evidence.

### supported_claims

M2975 supports these bounded claims:

```text
the nonzero residual training-admission branch is complete through trace-panel materialization and result audit
M2973/M2974 preserve 43 future training candidates, 13 success identity guards, and 11 stale guardrails
actor observation/action remains 72/action 3
hidden/oracle/future-target objective/admission/verdict labels remain actor-invisible
the branch has a concrete residual fitting blocker: raw deployable traces are not persisted
the next evidence-changing question is deployable trace capture, not residual fitting
```

These are process, accounting, and route-selection claims only.

### falsified_claims

M2975 rejects direct positive interpretation of M2973/M2974:

```text
residual fitting readiness is established: false
a nonzero residual head has been fitted, trained, or selected: false
repair success has been measured: false
validation readiness or validation result is established: false
controller, source, task, profile, checkpoint, or candidate ranking is supported: false
winner selection or checkpoint promotion occurred: false
paper evidence, current-sim verdict, high-fidelity readiness/result, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence is produced: false
```

M2975 also rejects another metadata-only trace materialization or audit before a
raw deployable trace-capture route is designed or the branch pivots/stops.

### failure_taxonomy_summary

The behavioral failure taxonomy remains:

```text
off_track: 35 / 56
collision: 7 / 56
speed_too_low: 1 / 56
diagnostic_success: 13 / 56
```

The active blocker taxonomy is now:

```text
metric_artifact: trace metadata is available but raw deployable traces are not persisted
lineage_invalid risk: fitting from metadata-only rows would break M2972/M2974 boundaries
proof_washout risk: another static trace panel could hide the missing raw-trace blocker
objective_overfit risk: fitting only offtrack rows without success/collision/speed guards remains forbidden
```

The 13 success rows remain identity guards, and the 11 stale fixed-source rows
remain protected guardrails outside training, validation, paper, high-fidelity,
and self-ID denominators.

### public_gate_overfit_risk

Public-gate overfit risk is medium. The branch has not tuned a residual model,
but it has spent several milestones on one current-sim actor-head delta surface.
The next route must therefore either produce a new raw trace-capture contract or
stop/pivot. It must not add another static accounting artifact that leaves
`raw_trace_persisted_count: 0` unchanged.

M2975 rejects:

```text
direct residual fitting from M2973 metadata-only rows
direct training from candidate labels without deployable observation/action traces
offtrack-only fitting that drops collision, speed-floor, success, or stale guardrails
ranking source families, task families, profiles, checkpoints, controllers, or candidates
claiming repair success, validation readiness, performance, paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence
```

### next_branch_decision

Decision:

```text
continue_to_m2976_deployable_trace_capture_design
```

M2976 must be design-only. It may define exactly one bounded deployable
trace-capture route, pivot, or stop state for the M2973/M2974 surface. The
design must specify the raw trace row contract, observation/action tensor
schema, candidate/guard coverage, actor 72/action 3 preservation, no hidden or
oracle actor inputs, and the gate that would reject metadata-only trace rows.

M2976 must not execute reset, step, rollout, replay, validation, training, PPO,
residual fitting, ranking, winner selection, checkpoint mutation, checkpoint
promotion, repair-success, performance, paper, current-sim, high-fidelity,
finite-window-vs-GRU, full-driver, or self-ID claims.
