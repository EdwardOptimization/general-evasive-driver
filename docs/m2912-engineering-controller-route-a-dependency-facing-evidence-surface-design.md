# M2912 Engineering Controller Route A Dependency-Facing Evidence Surface Design

## Metadata

- status: completed
- decision: `admit_m2913_route_a_dependency_facing_evidence_surface_materialization_preflight`
- manifest: `experiments/manifests/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.json`
- design artifact: `docs/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.md`
- parent synthesis: `docs/m2911-engineering-controller-route-a-post-route-b-source-insufficient-dependency-facing-synthesis.md`
- Route B closure: `docs/m2910-paper-route-l0-l1-l2-l3-capability-prediction-post-source-acquisition-continuation-or-pivot-synthesis.md`
- Route A weak diagnostic synthesis: `docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md`
- Route C source blocker design: `docs/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.md`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2913-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-preflight.json`
- next: `m2913-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-preflight`

## Design Decision

M2912 admits exactly one next action:

```text
materialize a machine-auditable Route A dependency-facing evidence surface
from existing post-M2470 artifacts before any new execution
```

Formal decision:

```text
admit_m2913_route_a_dependency_facing_evidence_surface_materialization_preflight
```

M2912 is design-only. It does not reset, step, roll out, replay, validate,
train, rank, promote, fetch, configure, build, import, link, start a backend,
or claim model quality, driver performance, paper evidence, current-sim verdict,
high-fidelity validation, full-driver completion, finite-window-vs-GRU evidence,
or self-ID evidence.

## Design Inputs

The next Route A surface must carry three recent constraints explicitly:

```text
Route B constraint:
  M2910 closes the fresh/source-diverse repair/source-acquisition branch as
  source-family-insufficient. Candidate-support 24 is not enough because
  independent source-family evidence remains 0.

Route A constraint:
  M2879 preserves weak post-package fresh diagnostic evidence. The latest
  11-row fixed surface produced 3 success 0 collision and 8 off_track outcomes
  and cannot be rebranded as validation readiness.

Route C constraint:
  M2883 keeps Chrono/HF3 stopped under source_unavailable. Route A material
  must not imply configure build import reset rollout or high-fidelity readiness.
```

## Surface Purpose

The M2913 surface should answer a narrower engineering question:

```text
Which actor-safe current-simulator Route A artifacts can support a materially
different engineering-controller evidence surface after Route B source-family
repair has closed insufficient and Route C remains source-unavailable?
```

This is not a paper self-ID surface. It is an engineering-controller evidence
inventory/materialization surface that can later admit one bounded execution or
stop decision.

## Candidate Row Families

M2913 should materialize these candidate families if the source artifacts are
present and boundary-clean.

### C1: Route A Source-Diverse Closed-Loop Diagnostics

Purpose:

```text
find post-M2470 Route A closed-loop diagnostic rows that are not the exhausted
M2877 fixed 11-row surface
```

Candidate sources may include prior Route A source-diverse failure taxonomy,
scenario-role metric, recoverability-window, clearence/offtrack, and
action-response diagnostic artifacts. M2913 must resolve paths from existing
repo-local docs/manifests rather than invent row counts.

Admission rule:

```text
admit as candidate context only if actor 72/action 3 is preserved and row source
identity can be tracked without hidden/oracle actor input
```

### C2: Weak Diagnostic Failure Context

Purpose:

```text
carry M2877/M2879 weak Route A results as failure context and exclusion pressure
```

The M2877 3/0/8 outcome surface is useful for failure taxonomy and route
selection, but it must not enter ordinary success denominators.

Admission rule:

```text
M2877 rows are diagnostic_context or exclusion_context unless M2913 identifies a
different source axis and denominator policy
```

### C3: Engineering Readiness And Runtime Context

Purpose:

```text
preserve deployable-controller practical constraints: actor contract,
runtime/inference-cost context, package limitations, known failure taxonomy, and
guardrail boundaries
```

These rows can guide materialization and later execution design, but they are
not driver-performance evidence by themselves.

### C4: Route B Source-Insufficient Context

Purpose:

```text
keep M2910 source-family insufficiency visible so Route A does not reuse Route B
candidate-support rows as paper proof or source-family repair
```

Admission rule:

```text
Route B rows may enter only as route_context or exclusion_context
```

### C5: Route C Source-Unavailable Context

Purpose:

```text
keep high-fidelity dependency blockers visible while Route A continues in
current-sim engineering mode
```

Admission rule:

```text
Route C rows may enter only as dependency_context or exclusion_context
```

## Exclusion Families

M2913 must explicitly mark these exclusions:

```text
same_family_route_b_acquisition_rows:
  not source-family proof and not paper denominator

m2877_fixed_post_package_rows:
  diagnostic context only unless a different source axis is proven

route_c_source_unavailable_rows:
  dependency context only and not high-fidelity readiness

protected_public_or_package_guard_rows:
  guard/exclusion context only

hidden_oracle_actor_input_rows:
  rejected boundary violation

future_target_actor_input_rows:
  rejected boundary violation
```

## Denominator Policy

M2913 should materialize a denominator policy table with at least these labels:

```text
ordinary_engineering_candidate:
  may be considered for a later Route A execution denominator only after a
  result audit confirms actor-safe source identity and non-stale surface status.

diagnostic_context_only:
  may explain failures or route decisions but cannot support performance
  claims.

guard_or_exclusion_only:
  protects known boundaries and cannot be used as success proof.

route_b_context_only:
  preserves source-family insufficiency and paper-route blocker state.

route_c_dependency_context_only:
  preserves source_unavailable and high-fidelity blocker state.

rejected_boundary_violation:
  hidden/oracle/future-target or actor-contract violation.
```

No row may become a validation, promotion, paper, high-fidelity, or self-ID
denominator in M2913.

## Failure Taxonomy

M2913 must write failure taxonomy rows covering:

```text
source_identity_unresolved:
  row cannot be traced to a source artifact or task-source identity.

stale_fixed_surface:
  row belongs to an exhausted fixed diagnostic surface.

route_b_source_family_insufficient:
  row would rely on same-family Route B acquisition.

route_c_dependency_unavailable:
  row would require unavailable high-fidelity source/build/reset gates.

actor_contract_violation:
  row would require hidden/oracle/future-target actor input or action mismatch.

denominator_violation:
  row would enter validation, paper proof, or ordinary success denominator
  without audit.

candidate_materialization_ok:
  row is claim-safe for later materialization audit only.
```

These local labels supplement the harness-level process-v2 taxonomy and do not
replace it.

## Required M2913 Outputs

M2913 should write these artifact families:

```text
summary.json
route_context_rows.csv
candidate_family_rows.csv
exclusion_family_rows.csv
denominator_policy_rows.csv
failure_taxonomy_rows.csv
actor_contract_rows.csv
claim_boundary_rows.csv
gate_rows.csv
run_state.json
experiments/manifests/m2914-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-result-audit.json
```

M2913 should not run policy actions. It should inspect and materialize a
machine-checkable evidence surface only.

## Claim Boundary

M2912 supports only:

```text
M2913 is admitted as a bounded materialization preflight for a Route A
dependency-facing evidence surface.
```

M2912 does not support:

```text
driver performance: false
validation readiness: false
current-sim verdict: false
high-fidelity readiness or result: false
paper evidence: false
finite-window-vs-GRU evidence: false
self-ID evidence: false
model-quality ranking: false
checkpoint promotion: false
```

## M2913 Admission Contract

M2913 is admitted as:

```text
m2913-engineering-controller-route-a-dependency-facing-evidence-surface-materialization-preflight
```

M2913 must:

```text
read this M2912 design and the M2911/M2910/M2879/M2883 parent artifacts;
materialize candidate, exclusion, denominator, failure-taxonomy, actor-contract,
claim-boundary, and gate rows;
preserve actor 72/action 3 and no hidden/oracle/future-target actor input;
preserve Route B source-family insufficiency and Route C source_unavailable;
register M2914 result-audit manifest;
avoid reset, step, rollout, replay, validation, training, ranking, promotion,
dependency execution, performance, paper, high-fidelity, full-driver,
finite-window-vs-GRU, and self-ID claims.
```
