# M2911 Engineering Controller Route A Post Route B Source-Insufficient Dependency-Facing Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_route_a_dependency_facing_evidence_surface_design`
- manifest: `experiments/manifests/m2911-engineering-controller-route-a-post-route-b-source-insufficient-dependency-facing-synthesis.json`
- synthesis artifact: `docs/m2911-engineering-controller-route-a-post-route-b-source-insufficient-dependency-facing-synthesis.md`
- parent synthesis: `docs/m2910-paper-route-l0-l1-l2-l3-capability-prediction-post-source-acquisition-continuation-or-pivot-synthesis.md`
- Route A parent synthesis: `docs/m2879-engineering-controller-route-a-post-package-refresh-fresh-closed-loop-evidence-result-synthesis.md`
- Route C blocker design: `docs/m2883-engineering-controller-route-c-hf3-chrono-next-dependency-gate-or-stop-design.md`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design.json`
- next: `m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design`

## Synthesis Decision

M2911 selects exactly one next action:

```text
continue to a bounded Route A dependency-facing evidence surface design
```

Formal decision:

```text
continue_to_route_a_dependency_facing_evidence_surface_design
```

This is not a return to the same Route A fixed diagnostic surface. M2912 must
design a new actor-safe engineering-controller evidence surface that explicitly
accounts for:

```text
M2910: Route B source-family insufficiency after candidate-support acquisition
M2879: weak Route A post-package fresh diagnostics
M2883: Route C Chrono source_unavailable blocker
```

M2911 does not execute reset, rollout, replay, validation, training, dependency
acquisition, configure, build, import, link, backend reset, step, ranking,
promotion, or paper work.

## Evidence Summary

Route B state after M2910:

```text
fixed source-acquisition rows executed: 34
execution failures: 0
candidate-support evidence added: 24
independent source-family evidence added: 0
same-family source-family rejection: 17
repaired candidate projections: 17
projected tasks/profile-tasks/target-families: 17/204/5
design targets satisfied: false
```

Route A state from M2879:

```text
post-package fresh diagnostic surface executed: 11/11
diagnostic success/collision/off_track: 3/0/8
ordinary success denominator allowed: false
driver performance claim: false
validation readiness claim: false
```

Route C state from M2883:

```text
Chrono source root exists: false
CMakeLists.txt exists: false
outcome: source_unavailable_claim_safe
configure/build/import/reset/rollout admitted: false
```

The active route problem is therefore not a missing document. It is a route
selection problem: Route B cannot progress from same-family acquisition, Route
C cannot execute while source is unavailable, and Route A needs a new evidence
surface that is not a stale fixed-row replay.

## Route Options

### Option 1: Continue Route B Acquisition

Rejected.

M2910 already closed the current Route B fresh-panel repair/source-acquisition
branch. More same-family execution would not add independent source-family
evidence and would create local-search churn.

### Option 2: Direct Route B Model-Quality Or Paper Work

Rejected.

The Route B paper plans require source-diverse task evidence and a fair
L0/L1/L2/L3 comparison before model-quality, finite-window-vs-GRU, or self-ID
claims. M2908/M2909/M2910 preserve the opposite result for the current panel:
candidate-support improved, source-family independence did not.

### Option 3: Direct Route C Dependency Execution

Rejected.

M2883 keeps Chrono stopped under source_unavailable. M2911 cannot fetch, clone,
configure, build, install, import, link, reset, step, smoke test, or validate a
high-fidelity backend.

### Option 4: Direct Route A Execution

Rejected for the immediate next milestone.

M2879 already warns against another direct fixed-surface Route A execution after
the weak 3/0/8 post-package diagnostic result. A new execution could be
admissible later only after a design identifies a materially different evidence
surface, denominator policy, guardrail exclusions, and failure taxonomy.

### Option 5: Route A Dependency-Facing Evidence Surface Design

Selected.

M2912 should design the next Route A evidence surface without executing it. The
design must answer:

```text
which existing Route A artifacts can support a materially different evidence
surface;
which fixed or protected rows must stay diagnostic-only or guard-only;
how Route B source-family insufficiency constrains source reuse;
how Route C source_unavailable constrains high-fidelity claims;
what execution candidate rows would change engineering-controller evidence if
later executed;
what claim, denominator, and actor-contract boundaries prevent overclaiming.
```

### Option 6: Stop

Rejected as a project-level stop.

The current Route B branch is closed and Route C execution is blocked, but
Route A still has a claim-safe design path for actor-safe engineering evidence.

## Supported Claims

M2911 supports only these claims:

```text
Route B source-family repair should not continue through same-family execution.

Route C high-fidelity execution remains blocked under source_unavailable.

Route A should not immediately repeat fixed diagnostic execution.

One bounded Route A dependency-facing evidence surface design is admissible as
the next task.
```

These are process and route-selection claims only.

## Falsified Claims

M2911 rejects:

```text
M2910 source-family insufficiency is solved by candidate-support count: false
Route B model-quality or self-ID evidence is ready: false
Route C dependency execution is ready: false
Route A weak diagnostics prove driver performance: false
another direct fixed-surface Route A execution is justified without design: false
driver performance changed: false
current-sim verdict changed: false
high-fidelity validation changed: false
finite-window-vs-GRU verdict changed: false
self-ID evidence changed: false
```

## Failure Taxonomy Summary

Controlled or inactive after M2911:

```text
contract_violation:
  controlled by preserving actor 72/action 3 and no hidden/oracle/future-target
  actor input.

lineage_invalid:
  controlled by connecting M2910 Route B insufficiency, M2879 Route A weak
  diagnostics, and M2883 Route C source_unavailable before selecting M2912.

metric_artifact:
  controlled by rejecting diagnostic rows and acquisition rows as ordinary
  validation denominators.

proof_washout:
  controlled by preserving Route B paper and self-ID separation.
```

Still active:

```text
behavior_regression:
  active because Route A's latest fresh diagnostic execution had 8/11 off_track
  outcomes.

scenario_sampling_failure:
  active because Route B source-family diversity remains insufficient.

objective_overfit:
  active unless M2912 designs a materially different Route A evidence surface.

high_fidelity_dependency_gap:
  active because Route C source remains unavailable.

self_id_gap:
  active because no fair source-diverse L0/L1/L2/L3 panel is admitted.
```

## Public Gate Overfit Risk

Public-gate overfit risk is high for repeating either of the exhausted local
surfaces:

```text
Route B same-family source-acquisition rows
Route A post-package fixed diagnostic rows
```

M2912 reduces that risk only if it treats those rows as context, guardrails, or
negative evidence, not as ordinary denominators or proof rows. It must identify
a different evidence increment before any later execution.

## M2912 Admission Contract

M2912 is admitted as:

```text
m2912-engineering-controller-route-a-dependency-facing-evidence-surface-design
```

M2912 must:

```text
write a Route A evidence surface design before execution;
name candidate row families and exclusion families;
preserve actor 72/action 3 and no hidden/oracle actor inputs;
keep Route B source-family insufficiency visible;
keep Route C source_unavailable visible;
define claim boundaries, denominator policy, and failure taxonomy;
register at most one follow-up manifest;
avoid reset, rollout, replay, validation, training, ranking, promotion,
dependency execution, model-quality, paper, current-sim, high-fidelity,
full-driver, finite-window-vs-GRU, and self-ID claims.
```
