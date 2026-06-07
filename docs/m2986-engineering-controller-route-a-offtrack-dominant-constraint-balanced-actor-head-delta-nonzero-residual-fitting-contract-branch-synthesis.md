# M2986 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Contract Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2987_fitting_contract_materialization_preflight`
- manifest: `experiments/manifests/m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-branch-synthesis.json`
- synthesis artifact: `docs/m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-branch-synthesis.md`
- parent design: `docs/m2985-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.md`
- parent audit: `docs/m2984-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-tensor-materialization-result-audit.md`
- parent target tensors: `runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight/summary.json`
- route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2987-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-preflight.json`
- next: `m2987-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-materialization-preflight`

M2986 synthesizes the M2976-M2985 Route A actor-head delta nonzero residual
target and fitting-admission chain. The branch has produced real trainer-side
target tensor artifacts, but those artifacts are still not target-quality
validated and do not yet define a fitting contract. The synthesis therefore
continues to one bounded contract materialization preflight, not fitting.

## Synthesis Questions

### evidence_summary

The accepted evidence chain is:

```text
M2976: designed deployable trace capture after raw traces blocked fitting.
M2977: captured raw actor-view observation/action/response traces.
M2978: accepted trace capture as complete and claim-safe.
M2979: rejected direct residual fitting from traces without numeric targets.
M2980: designed target materialization.
M2981: materialized target-source feasibility rows.
M2982: accepted target-source feasibility as complete and claim-safe.
M2983: materialized numeric target tensors.
M2984: accepted target tensor artifacts as complete and claim-safe.
M2985: rejected direct fitting and routed to synthesis before contract materialization.
```

The accepted M2983/M2984 accounting is:

```text
status_pass: true
gate_matrix_pass: true
candidate target tensor rows: 43
target tensor files: 56
success identity zero-target guards: 13
stale guardrail exclusions: 11
offtrack target rows: 35
collision target rows: 7
speed-floor target rows: 1
actor observation/action: 72/action 3
target_action_delta_abs_max: 0.08
target_loss_weight_sum: 4204.0
target labels actor-visible: false
target provenance actor-visible: false
target_quality_validated: false
residual fitting/training/validation/ranking run: false
```

The route-plan constraint from `docs/post-m2470-route-plan.md` remains active:
current-sim artifacts are useful for fast engineering diagnostics, but they
must not become the main loop or be interpreted as paper, current-sim,
high-fidelity, finite-window-vs-GRU, full-driver, or self-ID evidence.

### supported_claims

M2986 supports these bounded claims:

```text
the branch has complete raw trace, target-source, and target tensor artifacts through M2985
M2983/M2984 preserve 43 candidate target tensor rows, 13 success identity zero-target guards, and 11 stale exclusions
actor observation/action remains 72/action 3
target labels and target provenance remain actor-invisible
direct residual fitting remains blocked by missing fitting contracts and target_quality_validated false
one bounded fitting-contract materialization preflight is justified before any fitting can be reconsidered
```

These are synthesis, accounting, and route-selection claims only.

### falsified_claims

M2986 rejects direct positive interpretation of M2983-M2985:

```text
target quality is validated: false
residual fitting readiness is established: false
a nonzero residual head has been fitted, trained, validated, ranked, or selected: false
repair success has been measured: false
controller, source, task, profile, checkpoint, or candidate ranking is supported: false
winner selection or checkpoint promotion occurred: false
paper evidence, current-sim verdict, high-fidelity readiness/result, full-driver completion, finite-window-vs-GRU evidence, or self-ID evidence is produced: false
```

M2986 also rejects another open-ended current-sim artifact loop. The follow-up
must be the specific M2987 fitting-contract materialization preflight or the
branch must pivot/stop.

### failure_taxonomy_summary

The target family taxonomy is:

```text
offtrack_recovery_residual_objective: 35 / 43 target rows
collision_clearance_residual_objective: 7 / 43 target rows
speed_floor_context_guard_objective: 1 / 43 target rows
success_identity_zero_target_guard: 13 guard rows
stale_fixed_source_guardrail_exclusion: 11 excluded rows
```

The active blocker taxonomy is:

```text
contract_violation risk: fitting without split, denominator, mask, weight, guard, stale-exclusion, and side-effect contracts would break the accepted boundary
lineage_invalid risk: target tensors could be misread as target-quality validation
objective_overfit risk: offtrack-dominant target rows could drown collision, speed-floor, success, and stale guardrails
proof_washout risk: another static artifact could hide that no fitting, validation, or performance evidence exists
metric_artifact risk: target_loss_weight_sum and target_action_delta_abs_max are artifact checks, not performance metrics
```

The 13 success rows remain zero-target guards, and the 11 stale fixed-source
rows remain protected outside fitting, validation, paper, high-fidelity, and
self-ID denominators.

### public_gate_overfit_risk

Public-gate overfit risk is medium. The branch has spent many milestones on a
single current-sim actor-head delta surface, so M2986 must prevent static
infrastructure drift. The reason to continue once is that M2983 changed the
artifact state: numeric target tensors now exist. A fitting contract is the
minimal guard needed before those tensors can be consumed or rejected.

M2986 rejects:

```text
direct residual fitting from M2983 target tensors
offtrack-only fitting that drops collision, speed-floor, success, or stale guardrails
target quality validation by assertion
ranking source families, task families, profiles, checkpoints, controllers, or candidates
claiming repair success, validation readiness, performance, paper, current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID evidence
```

### next_branch_decision

Decision:

```text
continue_to_m2987_fitting_contract_materialization_preflight
```

M2987 must be infrastructure-only. It may materialize fitting-contract rows for
dataset loading, split denominators, target masks, loss weights, success
zero-guard binding, stale exclusion binding, actor input exclusion, checkpoint
side-effect guards, claim boundaries, and gate rows.

M2987 must not fit, train, validate, rank, select, promote, mutate
checkpoints, or claim repair-success, performance, paper, current-sim,
high-fidelity, finite-window-vs-GRU, full-driver, or self-ID evidence. Its
follow-up must be a result audit before any later fitting-admission decision.
