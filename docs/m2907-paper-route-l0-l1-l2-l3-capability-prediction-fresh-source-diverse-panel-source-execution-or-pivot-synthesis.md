# M2907 Paper Route L0/L1/L2/L3 Capability-Prediction Fresh Source-Diverse Panel Source Execution Or Pivot Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_to_bounded_source_acquisition_execution_preflight`
- manifest: `experiments/manifests/m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis.json`
- synthesis artifact: `docs/m2907-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-execution-or-pivot-synthesis.md`
- parent audit: `docs/m2906-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-repair-source-acquisition-materialization-result-audit.md`
- parent materialization summary: `runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/summary.json`
- parent acquisition rows: `runs/m2905_paper_route_l0_l1_l2_l3_capability_prediction_fresh_source_diverse_panel_repair_source_acquisition_materialization_preflight/acquisition_required_rows.csv`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight.json`
- next: `m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight`

## Synthesis Decision

M2907 selects exactly one next action:

```text
run one bounded source-acquisition execution preflight over the M2905
acquisition-required surface
```

Formal decision:

```text
continue_to_bounded_source_acquisition_execution_preflight
```

This continues Route B only through evidence-producing source acquisition. It
does not admit another static repair-only design/materialization/audit loop, and
it does not admit validation, model-quality ranking, paper proof,
finite-window-vs-GRU claims, current-sim verdicts, high-fidelity verdicts,
full-driver claims, or self-ID claims.

## Evidence Summary

M2905/M2906 accepted the repair/source-acquisition accounting surface but
preserved a negative panel-readiness result:

```text
seed-gap repair rows: 34
candidate-support gap rows: 24
source-family gap rows: 17
dual-gap rows: 7
acquisition-required rows: 34
repaired-candidate projection rows: 0
projected fresh candidate tasks: 0
projected fresh candidate profile tasks: 0
projected source families: 0
projected task families: 0
projected target-family coverage: 0
projected design targets satisfied: false
```

The gap is no longer a missing accounting artifact. It is a real source
availability/execution gap:

```text
candidate_artifact_count>=2 gaps: 24
source_family_tag_count>=2 gaps: 17
dual gaps: 7
T4 rows: 15
T5 rows: 19
```

The claim boundaries remain clean:

```text
actor observation/action contract: 72/action 3
hidden_oracle_actor_input_required: false
future_target_actor_input_required: false
evaluator_targets_actor_visible: false
paper_holdout_admitted: false
preflight_only_split: true
claim_made_count: 0
target_actor_visible_count: 0
split_denominator_admitted_count: 0
```

## Route Options

M2907 considered four routes.

### Option 1: Source-Acquisition Execution

Admit one bounded execution preflight over the fixed M2905
`acquisition_required_rows.csv`.

This is the selected route because it can change the evidence surface: it can
produce new candidate-support and source-family artifacts or fail rows that
prove the Route B panel cannot be repaired from the current executable source
surface.

The execution must be bounded:

```text
input row set: exactly the 34 M2905 acquisition-required rows
execution source: existing repo-local executable workload/config/checkpoint rows
seed base: 290800
device: cpu
row substitution: forbidden
private holdout: false
validation denominator: false
paper proof denominator: false
ordinary success denominator: false
ranking or winner selection: false
```

### Option 2: Route A Pivot

Route A can produce closed-loop engineering-controller diagnostics, but M2907
does not select it yet because M2905 has a concrete source-acquisition surface
that has not been executed. Route A remains the fallback if M2908 reports that
the acquisition surface cannot produce fresh/source-diverse support.

### Option 3: Route C Pivot

Route C remains important, but the recent Route C/HF3 Chrono branch stopped
under source-unavailable evidence before Route B began. M2907 does not re-enter
Route C immediately because the current blocker is a fixed Route B acquisition
surface that can be tested without external high-fidelity source setup.

### Option 4: Stop Route B

Stopping Route B now would be premature. M2905/M2906 did not show that source
acquisition is impossible; they showed only that existing repo-local support is
insufficient without a bounded acquisition execution attempt.

## Supported Claims

M2907 supports only these claims:

```text
M2905/M2906 closed the static repair-accounting loop for the current Route B
fresh/source-diverse panel expansion.

The next Route B step must be evidence-producing source acquisition or a later
pivot/stop, not another static repair-only artifact.

One bounded source-acquisition execution preflight is admitted because the 34
acquisition-required rows are fixed, claim-safe, and auditable.
```

These are route and workflow claims. They are not driver-performance,
model-quality, paper, current-sim verdict, high-fidelity, full-driver,
finite-window-vs-GRU, or self-ID claims.

## Falsified Claims

M2907 rejects:

```text
M2905/M2906 make the fresh/source-diverse panel ready: false
M2905/M2906 validate prediction quality: false
M2905 acquisition-required rows are paper proof: false
source-singleton rows may enter validation denominators: false
guard rows may enter ordinary success denominators: false
another static repair-only loop is justified: false
Route C dependency readiness has changed: false
Route A or Route C is permanently rejected: false
driver performance changed: false
finite-window-vs-GRU verdict changed: false
self-ID evidence changed: false
```

## Failure Taxonomy Summary

Controlled or inactive after M2907:

```text
lineage_invalid:
  controlled by M2905/M2906 accepted parent artifacts and fixed row set.

contract_violation:
  controlled by actor 72/action 3, evaluator-only future targets, and no hidden
  or oracle actor input.

proof_washout:
  controlled by keeping source-singleton, guard, public-reference, and
  acquisition-required rows out of proof and denominators.
```

Still active:

```text
scenario_sampling_failure:
  active because the accepted surface still has zero repaired projections.

objective_overfit:
  active unless M2908 produces source-diverse support instead of reusing stale
  public rows.

seed_fragility:
  active until source acquisition creates fresh rows or fails them explicitly.

behavior_regression:
  active because Route B capability prediction is not closed-loop controller
  behavior evidence.

high_fidelity_dependency_gap:
  active because Route C source availability has not changed.

self_id_gap:
  active because no fair L0/L1/L2/L3 source-diverse panel has been admitted.
```

## Public Gate Overfit Risk

Public-gate overfit risk is medium. The M2905 row set is derived from prior
public/reference and source-singleton surfaces, so M2908 must treat those rows
as acquisition candidates only. A row becomes a repaired candidate only if it
adds independent candidate/source-family support without weakening M2901
thresholds or exposing evaluator-only targets to actor input.

## M2908 Admission Contract

M2908 is admitted as a bounded source-acquisition execution preflight:

```text
m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight
```

M2908 must:

```text
read the fixed M2905 acquisition_required_rows.csv
resolve each row against existing repo-local executable workload artifacts
execute only bounded source-acquisition diagnostics for resolved rows
write explicit failure rows for unresolved or invalid rows
materialize candidate-support and source-family acquisition evidence
project repaired candidates only when original M2901 criteria remain satisfied
register a result-audit manifest before interpretation
```

M2908 required output families:

```text
summary.json
source_acquisition_input_rows.csv
execution_resolution_rows.csv
source_acquisition_execution_rows.csv
candidate_support_evidence_rows.csv
source_family_evidence_rows.csv
acquisition_failure_rows.csv
repaired_candidate_projection_rows.csv
split_boundary_rows.csv
target_boundary_rows.csv
actor_contract_rows.csv
claim_rows.csv
gate_rows.csv
run_state.json
experiments/manifests/m2909-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-result-audit.json
```

Allowed in M2908:

```text
bounded reset/step/policy-action execution only for the fixed acquisition rows
diagnostic artifact generation
failure classification
candidate/source-family evidence materialization
```

Forbidden in M2908:

```text
training or PPO
replay expansion outside the fixed row set
private holdout use
row substitution
threshold weakening
ranking controllers or source families
winner selection
checkpoint promotion
validation or paper proof denominators
model-quality verdicts
driver-performance verdicts
finite-window-vs-GRU verdicts
current-sim verdicts
high-fidelity validation claims
full ideal driver completion claims
level3 self-ID claims
```

## Next Route

The next task is:

```text
m2908-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-source-acquisition-execution-preflight
```

If M2908 cannot produce repaired candidates without weakening the contract, the
M2909 audit must preserve that negative result and route to Route A, Route C, or
stop. It must not start another static repair-only loop.
