# M2985 Engineering Controller Route A Actor-Head Delta Nonzero Residual Fitting Admission Design

## Metadata

- status: completed
- decision: `route_to_m2986_fitting_contract_branch_synthesis_before_m2987_contract_materialization`
- manifest: `experiments/manifests/m2985-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-admission-design.json`
- parent audit: `docs/m2984-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-target-tensor-materialization-result-audit.md`
- parent target tensors: `runs/m2983_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_target_tensor_materialization_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-branch-synthesis.json`
- next: `m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-branch-synthesis`

## Design Decision

M2985 routes to one branch synthesis before any fitting-contract
materialization preflight.

Formal decision:

```text
route_to_m2986_fitting_contract_branch_synthesis_before_m2987_contract_materialization
```

M2984 accepts M2983 target tensor materialization as complete and claim-safe,
but it explicitly rejects target quality and residual fitting readiness. M2985
therefore does not admit fitting, training, validation, ranking, promotion, or
checkpoint mutation.

M2985 also does not directly open the next non-synthesis materialization
milestone. The branch has accumulated enough Route A current-sim
infrastructure since the last synthesis that the local-search cadence must
fire before another contract preflight. The next step is M2986 branch
synthesis. If M2986 chooses `continue`, the concrete contract materialization
route is M2987.

## Evidence Review

The accepted M2983/M2984 artifact state is:

```text
status_pass: true
gate_matrix_pass: true
candidate target tensor rows: 43
target tensor files: 56
success identity zero-target guards: 13
stale guardrail exclusions: 11
actor observation/action: 72/action 3
target_action_delta_abs_max: 0.08
target_loss_weight_sum: 4204.0
target labels actor-visible: false
target provenance actor-visible: false
target_quality_validated: false
residual fitting/training/validation/ranking run: false
```

The candidate target family split remains:

```text
offtrack_recovery_residual_objective: 35
collision_clearance_residual_objective: 7
speed_floor_context_guard_objective: 1
```

The success identity rows remain zero-target guards, and the stale fixed-source
guardrails remain exclusions only.

## Direct Fitting Admission Audit

M2985 rejects direct fitting because the accepted target tensors still do not
define the full fitting contract:

```text
dataset loader contract: absent
train/guard split contract: absent
candidate denominator contract: absent
loss normalization contract: absent
target validity mask binding contract: absent
target loss weight binding contract: absent
success identity zero-target handling contract: absent
stale exclusion enforcement contract: absent
target-quality acceptance contract: absent
checkpoint mutation policy: absent
post-fit audit gate: absent
```

M2983 proves bounded tensor materialization, not that those tensors are
sufficient to update a residual head. The `target_quality_validated=false`
state must stay visible until a later contract and audit explicitly decide how
targets may be consumed.

## M2986 Synthesis Contract

M2986 must synthesize the M2976-M2985 Route A actor-head delta nonzero residual
chain before opening another materialization milestone. It must answer:

```text
evidence_summary
supported_claims
falsified_claims
failure_taxonomy_summary
public_gate_overfit_risk
next_branch_decision
```

The synthesis must decide whether the branch should continue to M2987 fitting
contract materialization, pivot to artifact repair, stop, or promote to a new
branch. It must preserve the route-plan constraint from
`docs/post-m2470-route-plan.md`: do not let static current-sim infrastructure
become the main loop or turn process artifacts into paper, performance,
current-sim, high-fidelity, finite-window-vs-GRU, full-driver, or self-ID
evidence.

## M2987 Contract If Continued

If M2986 chooses `continue`, M2987 must materialize fitting-admission contracts
only. It must consume the M2983 target tensor directory, M2984 audit, M2985
design, and M2986 synthesis, then write machine-checkable rows for:

```text
dataset surface and loader contract
candidate split and fitting denominator contract
target mask and target loss weight binding
success identity zero-target guard binding
stale guardrail exclusion binding
actor input invisibility and forbidden metadata checks
checkpoint side-effect guards
target-quality not-yet-validated state
claim-boundary rows
gate matrix rows
```

M2987 may make a later fitting preflight possible only if the contract rows are
complete and claim-safe. It must not fit a residual, train a network, run
validation, rank candidates, select a winner, mutate checkpoints, or claim
repair success or driver performance.

## Actor And Guard Boundaries

M2985 preserves the current boundaries:

```text
actor observation/action: 72/action 3
actor input contract changed: false
target labels actor-visible: false
target provenance actor-visible: false
objective/admission/source/route/verdict labels actor-visible: false
hidden/oracle/future-target actor input: false
success identity positive targets: 0
stale guardrail target materializations: 0
stale guardrails in fitting denominator: false
```

The target tensors remain trainer-side artifacts. M2986 and any later M2987
contract must keep target metadata, objective families, provenance, route
decisions, and audit verdicts outside actor inputs.

## Supported Claims

M2985 supports only:

```text
M2983/M2984 provide complete bounded target tensor artifacts for 43 future
training candidates and 13 success identity zero-target guards.

M2983/M2984 preserve 11 stale guardrail exclusions, actor 72/action 3, and
actor-invisible target labels and provenance.

Direct residual fitting remains blocked until a fitting contract is
materialized and audited.

The next admissible route is M2986 fitting-contract branch synthesis.
```

These are design and admission-boundary claims only.

## Rejected Claims

M2985 rejects:

```text
direct residual fitting admitted from target tensors alone: false
target quality validated: false
residual fitting executed: false
residual training executed: false
validation/ranking/promotion executed: false
winner selected: false
checkpoint mutated: false
repair success proved: false
driver performance improved: false
paper/current-sim/high-fidelity/full-driver/finite-window-vs-GRU/self-ID evidence produced: false
```

## Route Contract

M2985 selects exactly one next route:

```text
m2986-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-fitting-contract-branch-synthesis
```

M2986 must be design/synthesis only. It must fail closed if the accepted target
tensors cannot justify a bounded next route without weakening target-quality,
guard, stale-exclusion, actor-input, checkpoint side-effect, or claim
boundaries. If it continues, its follow-up must be M2987 contract
materialization and then an M2988 result audit before any fitting, training,
validation, ranking, promotion, repair-success, performance, paper,
current-sim, high-fidelity, full-driver, finite-window-vs-GRU, or self-ID
claim.
