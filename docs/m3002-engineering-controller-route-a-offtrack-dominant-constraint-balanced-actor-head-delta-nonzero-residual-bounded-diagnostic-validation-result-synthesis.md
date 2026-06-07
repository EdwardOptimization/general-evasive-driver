# M3002 Engineering Controller Route A Nonzero Residual Bounded Diagnostic Validation Result Synthesis

## Metadata

- status: completed
- synthesis decision: `pivot`
- decision: `pivot_to_post_residual_stop_fresh_source_diverse_evidence_surface_design`
- manifest: `experiments/manifests/m3002-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-synthesis.json`
- synthesis artifact: `docs/m3002-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-synthesis.md`
- parent audit: `docs/m3001-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-diagnostic-validation-result-audit.md`
- parent diagnostic summary: `runs/m3000_engineering_controller_route_a_offtrack_dominant_constraint_balanced_actor_head_delta_nonzero_residual_bounded_diagnostic_validation_preflight/summary.json`
- governing route plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design.json`
- next: `m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design`

M3002 synthesizes the M2998-M3001 residual-head validation-contract and
diagnostic-execution chain. The chain is complete and claim-safe, but the
closed-loop diagnostic result is behavior-neutral relative to the parent
reference. This synthesis therefore closes the actor-head-delta nonzero
residual-head branch and pivots to a fresh source-diverse evidence-surface
design.

M3002 does not run reset, step, rollout, replay, validation, training, PPO,
private holdout, source build, adapter probe, external simulation, ranking,
winner selection, checkpoint mutation, checkpoint promotion, or success-rate
verdict computation.

## Synthesis Questions

### evidence_summary

M2998 continued exactly once from validation-contract synthesis to a bounded
validation-preflight design because M2993-M2997 had materialized the missing
wrapper, denominator, stale-exclusion, success-retention, parent-comparison,
side-effect, and claim-boundary surfaces.

M2999 admitted one diagnostic execution route only:

```text
candidate denominator: fixed M2996 43-row candidate validation denominator
success-retention denominator: fixed M2996 13-row success-retention denominator
stale fixed-source exclusions: 11 rows preserved outside validation/paper/self-ID denominators
parent comparison: report-only
ranking/winner/promotion/checkpoint mutation: false
validation-result/repair-success/performance/paper/current-sim/HF/FW-vs-GRU/self-ID claims: false
```

M3000 executed the bounded diagnostic route and wrote complete artifacts:

```text
status_pass: true
gate_matrix_pass: true
required_artifacts_present: true
candidate validation execution rows: 43
success-retention execution rows: 13
candidate validation failure rows: 0
stale rows executed: 0
actor observation/action: 72/3
residual abs max: 0.0016821095487102866
parent comparison report-only: true
ranking/winner/promotion/checkpoint mutation: false
```

M3000 diagnostic outcomes were:

```text
candidate rows:
  off_track: 35
  obstacle_collision: 7
  speed_too_low: 1

success-retention rows:
  success: 13
```

M3001 audited the result and found that every parent/candidate outcome pair
stayed in the same outcome bucket:

```text
off_track_noncollision_noncompletion -> off_track_noncollision_noncompletion: 35
collision_failure -> collision_failure: 7
speed_too_low_noncollision_noncompletion -> speed_too_low_noncollision_noncompletion: 1
success_obstacle_pass -> success_obstacle_pass: 13
```

This is useful negative evidence. The residual-head wrapper is executable and
bounded, but it did not change any closed-loop outcome bucket on the fixed
diagnostic denominator.

### supported_claims

M3002 supports only these bounded claims:

```text
M2998-M3001 form a complete and claim-safe residual-head validation-contract
and diagnostic-execution chain.

The M2993 read-only residual-head wrapper can be executed under actor 72/action
3 without actor-visible hidden/oracle target labels, target provenance, route
verdicts, paper labels, or privileged state.

M3000 produced complete current-sim diagnostic rows over the fixed M2996
candidate and success-retention denominators while preserving stale exclusions
and report-only parent comparison.

The M3000 result is behavior-neutral: all 56 parent/candidate outcome pairs
remain in the same bucket.

The actor-head-delta nonzero residual-head branch should stop as a local repair
route and pivot to a fresh evidence surface that is not the M2996/M3000 fixed
denominator.
```

These are process, diagnostic, and route-decision claims only.

### falsified_claims

M3002 rejects these interpretations:

```text
M3000 validates the residual head: false
M3000 shows repair success: false
M3000 improves the parent outcome distribution: false
M3000 supports ranking, winner selection, checkpoint promotion, or baseline replacement: false
M3000 supports driver performance, validation result, current-sim verdict,
paper evidence, high-fidelity validation, finite-window-vs-GRU evidence,
full-driver evidence, or self-ID evidence: false
another narrow actor-head-delta residual-head repair on the same denominator is
the next admissible research route: false
```

The behavior-neutral result also falsifies the narrow continuation premise from
M2998: one bounded diagnostic execution was legal, but the outcome does not
justify another residual-head materialization, fitting, wrapper, or audit loop
over the same surface.

### failure_taxonomy_summary

Controlled in M2998-M3001:

```text
contract_violation:
  controlled. Actor 72/action 3 and no hidden/oracle actor input were
  preserved.

lineage_invalid:
  controlled. M2993, M2996, M2998, M2999, M3000, and M3001 artifacts are
  traceable and audited.

metric_artifact:
  controlled for artifact completeness. Residual magnitude, row counts, and
  gate rows remain diagnostic fields, not performance metrics.

proof_washout:
  controlled by explicit claim-boundary rows and by M3001 rejection of
  validation, repair-success, performance, paper, and self-ID interpretations.
```

Active after M3002:

```text
behavior_regression_or_no_effect:
  active. The candidate does not change any parent outcome bucket and the
  candidate denominator remains dominated by off_track and collision outcomes.

objective_overfit:
  high if the next task keeps tuning the M2996/M3000 fixed current-sim surface.

scenario_sampling_failure:
  active for broad driver claims. The fixed denominator is a diagnostic surface,
  not a validation or distribution-level driver benchmark.

local_search:
  active if the branch produces another residual-head fitting, wrapper,
  validation-contract, or audit milestone without a new evidence surface.
```

### public_gate_overfit_risk

Public-gate overfit risk is high for continuing the current residual-head
branch. The branch has spent many milestones turning one offtrack-dominant
current-sim surface into target tensors, fitting contracts, wrapper contracts,
and diagnostic execution. That work preserved the safety boundary, but the
only closed-loop result is behavior-neutral.

Risk is high for:

```text
another M2996/M3000 denominator execution
another actor-head-delta residual fitting loop
another wrapper or validation-contract materialization loop
claiming target-quality validation from residual magnitude
ranking or promoting from report-only parent comparison
counting stale fixed-source rows in validation, paper, or self-ID denominators
turning current-sim diagnostic rows into a paper or self-ID claim
```

Risk is lower for a pivot that fixes a new denominator before execution:

```text
new evidence surface:
  post-residual-stop fresh source-diverse Route A diagnostic surface

required properties:
  excludes the M2996/M3000 fixed denominator
  excludes prior protected/current-sim surfaces already used for repair loops
  preserves actor 72/action 3 and no hidden/oracle inputs
  preserves Route C selected-platform dependency blockers
  records negative outcomes rather than hiding them
  routes to audit before interpretation
```

### next_branch_decision

Decision:

```text
pivot_to_post_residual_stop_fresh_source_diverse_evidence_surface_design
```

Admitted next milestone:

```text
m3003-engineering-controller-route-a-post-residual-stop-fresh-source-diverse-evidence-surface-design
```

M3003 must design a new fixed source-diverse Route A diagnostic surface before
any execution. It should select non-same-surface criteria and exclusion rules
for a later evidence-producing preflight, with at least these boundaries:

```text
exclude the M2996/M3000 fixed validation denominator
exclude stale fixed-source rows from validation, paper, and self-ID denominators
exclude prior protected surfaces used only as guardrails
do not reuse behavior-neutral residual-head execution as the optimization target
do not load, mutate, rank, select, or promote checkpoints
do not expose source family, task family, scenario role, target, route, outcome,
progress, success, or verdict labels to actor input
preserve actor observation shape 72 and action shape 3
preserve Route C/HF3 source dependency blocker until source or approved
dependency route is supplied
route to a materialization or execution preflight only if the design expands
evidence beyond fixed public residual-head rows
```

M3003 must not claim validation, repair success, driver performance, paper,
current-sim, high-fidelity, finite-window-vs-GRU, full-driver, or self-ID
evidence. If M3003 cannot identify a fresh evidence surface, it should stop the
Route A residual-adjacent continuation rather than reopen local repair.
