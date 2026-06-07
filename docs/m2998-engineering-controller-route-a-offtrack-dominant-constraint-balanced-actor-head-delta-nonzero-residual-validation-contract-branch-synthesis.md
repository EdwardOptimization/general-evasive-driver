# M2998 Engineering Controller Route A Actor-Head Delta Nonzero Residual Validation Contract Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- decision: `continue_to_m2999_bounded_validation_preflight_design`
- manifest: `experiments/manifests/m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis.json`
- synthesis artifact: `docs/m2998-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-validation-contract-branch-synthesis.md`
- parent audit: `docs/m2997-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-validation-contract-materialization-result-audit.md`
- parent materialization summary: `runs/m2996_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_validation_contract_materialization_preflight/summary.json`
- parent fitting summary: `runs/m2993_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_success_identity_guard_constrained_fitting_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2999-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-validation-preflight-design.json`
- next: `m2999-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-validation-preflight-design`

M2998 synthesizes the M2993-M2997 guard-constrained residual-head fitting and
validation-contract branch after the local-search guard blocked another
ordinary process-only validation design.

The synthesis decision is to continue exactly once, and only to a bounded
validation-preflight design. The reason is narrow: M2993-M2997 did not produce
closed-loop driver evidence, but they did materialize the wrapper, denominator,
stale-exclusion, success-retention, parent-comparison, side-effect, and claim
surfaces needed to decide whether one bounded validation execution preflight is
legal.

M2998 makes no validation, ranking, promotion, repair-success, performance,
paper, current-sim verdict, high-fidelity, finite-window-vs-GRU, full-driver,
or self-ID claim.

## Synthesis Questions

### evidence_summary

The accepted branch evidence is:

```text
M2993:
  status_pass: true
  gate_matrix_pass: true
  fitting rows: 43
  fitting samples: 4204
  initial weighted MSE: 0.0010713406183980136
  final weighted MSE: 0.001065189191153038
  M2990 success guard residual abs max: 0.07999999821186066
  M2993 success guard residual abs max: 0.00034158502239733934
  candidate residual-head artifact: present
  linear weight shape: 72 x 3
  action shape: 3
  target_quality_validated: false
  validation/ranking/promotion/checkpoint mutation: false

M2994:
  accepted M2993 as artifact-complete and claim-safe only
  rejected direct validation, repair-success, performance, paper, current-sim,
  high-fidelity, full-driver, finite-window-vs-GRU, and self-ID claims

M2995:
  admitted validation-contract materialization only
  did not admit environment validation, ranking, winner selection, promotion,
  performance measurement, private holdout, or checkpoint mutation

M2996:
  status_pass: true
  gate_matrix_pass: true
  validation contract rows: 43
  residual-head wrapper rows: 3
  parent comparison rows: 3
  success-retention rows: 13
  stale exclusion rows: 11
  actor input exclusion rows: 14
  checkpoint side-effect guard rows: 12
  residual artifact shape: 72 x 3 / action 3
  residual limit: 0.07999999821186066
  success-retention residual abs max: 0.00034158502239733934
  target_quality_validated: false
  validation/ranking/winner/promotion/checkpoint mutation: false

M2997:
  accepted M2996 as validation-contract materialization only
  rejected validation result, repair success, performance, paper, current-sim
  verdict, high-fidelity, full-driver, finite-window-vs-GRU, and self-ID claims
  routed to synthesis because the local-search guard rejected another ordinary
  process-only validation design
```

The chain is complete as a trainer-side artifact and validation-contract chain.
It is not complete as closed-loop validation evidence.

### supported_claims

M2998 supports these bounded claims:

```text
M2993-M2997 define a claim-safe residual-head artifact and validation-contract chain.

The accepted residual-head candidate is actor-shape compatible at observation
72/action 3 and remains read-only.

M2996 defines the missing pre-validation surfaces: residual-head wrapper,
candidate denominator, success-retention denominator, stale fixed-source
exclusions, parent comparison, actor-input exclusions, checkpoint side-effect
guards, and claim-boundary rows.

The next legal route can be a bounded validation-preflight design only if it
preserves read-only parent and candidate artifacts, report-only comparison,
success-retention accounting, stale exclusions, actor invisibility, and no
promotion or ranking.

Another process-only milestone is justified only as the final design gate
before a data-producing validation preflight, pivot, or stop decision.
```

These are branch synthesis and route-selection claims only.

### falsified_claims

M2998 rejects:

```text
M2993 or M2996 established target quality: false
M2993 or M2996 established closed-loop repair success: false
M2993 or M2996 improved driver performance: false
M2993 or M2996 produced paper evidence: false
M2993 or M2996 produced current-sim verdict evidence: false
M2993 or M2996 produced high-fidelity evidence: false
M2993 or M2996 produced finite-window-vs-GRU evidence: false
M2993 or M2996 produced full-driver or self-ID evidence: false
validation-contract materialization alone proves behavior retention: false
another ordinary process-only milestone without synthesis is justified: false
```

The materialized contracts are useful because they make a future bounded
validation-preflight design auditable. They do not validate the candidate.

### failure_taxonomy_summary

The active failure taxonomy is:

```text
proof_washout:
  repeated process artifacts can obscure the absence of closed-loop validation
  data.

objective_overfit:
  the residual head is fit on a narrow offtrack-dominant current-sim surface and
  can overfit trainer-side target tensors.

behavior_regression:
  success-retention rows must prevent already-successful traces from receiving
  behavior-changing residual action.

metric_artifact:
  fitting MSE and contract row counts are not target quality, validation
  success, or driver performance metrics.

contract_violation:
  validation execution would be invalid if target labels, target provenance,
  objective/admission/source/route/verdict labels, or paper labels become
  actor-visible, or if parent/candidate artifacts are mutated.

lineage_invalid:
  stale fixed-source rows must stay excluded from validation, paper, and self-ID
  denominators.
```

### public_gate_overfit_risk

Public-gate overfit risk is medium-high.

The branch has spent several milestones turning Route A current-sim blockers
into process surfaces. The post-M2470 route split still applies: current-sim is
a bounded engineering diagnostic layer, not paper, high-fidelity,
finite-window-vs-GRU, full-driver, or self-ID evidence by itself.

The reason to continue once is practical and bounded. M2996 created the
machine-checkable validation-contract surfaces that were previously missing.
A bounded validation-preflight design can now decide whether the next task is
allowed to produce closed-loop diagnostic data, must pivot to Route C/high
fidelity or interface work, or must stop.

M2998 rejects further materialization, audit, or design loops after M2999
unless M2999 either admits a data-producing diagnostic execution route, records
a concrete contract violation that must be repaired, pivots to high-fidelity or
interface work, or stops the branch.

### next_branch_decision

Decision:

```text
continue_to_m2999_bounded_validation_preflight_design
```

M2999 must be a bounded design-only validation-preflight decision. It must
specify:

```text
read-only parent checkpoint loading
read-only residual-head wrapper loading
actor observation/action contract: 72/3
candidate validation denominator: 43 M2996 validation rows
success-retention denominator: 13 M2996 success-retention rows
stale fixed-source exclusions: preserved and excluded from validation/paper/self-ID denominators
parent comparison: report-only, no ranking, no winner, no promotion
failure taxonomy and result-audit requirements
no target labels, target provenance, objective/admission/source/route/verdict labels, paper labels, or privileged state actor inputs
no private holdout, performance verdict, paper verdict, high-fidelity verdict, finite-window-vs-GRU verdict, full-driver verdict, or self-ID verdict
```

M2999 should fail closed if it cannot define a data-producing diagnostic
preflight without weakening the actor, stale-exclusion, checkpoint, side-effect,
comparison, or claim boundaries.
