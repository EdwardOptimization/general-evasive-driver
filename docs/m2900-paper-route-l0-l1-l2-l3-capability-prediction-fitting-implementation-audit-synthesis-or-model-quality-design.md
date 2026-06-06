# M2900 Paper Route L0/L1/L2/L3 Capability-Prediction Fitting Implementation Audit Synthesis Or Model-Quality Design

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_admit_m2901_fresh_source_diverse_panel_design`
- manifest: `experiments/manifests/m2900-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-audit-synthesis-or-model-quality-design.json`
- synthesis artifact: `docs/m2900-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-audit-synthesis-or-model-quality-design.md`
- parent audit: `docs/m2899-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-result-audit.md`
- parent fitting summary: `runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight/summary.json`
- parent fitting recipe: `runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight/fitting_recipe_rows.csv`
- parent optimizer diagnostics: `runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight/optimizer_step_rows.csv`
- parent profile diagnostics: `runs/m2898_paper_route_l0_l1_l2_l3_capability_prediction_fitting_implementation_preflight/profile_metric_diagnostic_rows.csv`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design.json`
- next: `m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design`

## Synthesis Decision

M2900 selects exactly one next action:

```text
admit a bounded fresh/source-diverse capability-prediction panel design
```

Formal decision:

```text
continue_admit_m2901_fresh_source_diverse_panel_design
```

This continues Route B, but it does not admit model-quality evaluation,
validation, profile ranking, winner selection, checkpoint promotion, paper
claims, finite-window-vs-GRU claims, current-sim or high-fidelity verdicts, or
self-ID claims. The accepted fitting implementation preflight is complete, but
its usable surface is still the small public 17-row panel. The next useful
action is therefore to design a fresh/source-diverse panel expansion before
any model-quality denominator is created.

## Evidence Summary

M2890-M2899 provide a complete and claim-safe Route B capability-prediction
preflight chain:

```text
M2890 modeling-contract design: completed
M2891 modeling-contract materialization: completed
M2892 modeling-contract materialization audit: completed
M2893 implementation preflight: completed
M2894 implementation result audit: completed
M2895 implementation branch synthesis: completed
M2896 fitting design: completed
M2897 fitting-design result audit: completed
M2898 fitting implementation preflight: completed
M2899 fitting implementation result audit: completed
```

Accepted M2898/M2899 fitting facts:

```text
status_pass: true
gate_matrix_pass: true
source task rows: 17
profile-task rows: 204
task_source_id split: smoke_fit 14, smoke_eval 3
target scalar dimension: 19
active target scalars: 13
available target entries: 221
fitting recipe rows: 12
task_source_id split rows: 17
target-normalization rows: 19
availability-mask rows: 323
optimizer-step rows: 4608
profile diagnostic rows: 72
baseline diagnostic rows: 53
overfit guard rows: 6
rollback rows: 7
claim rows: 16
gate rows: 13
run-local fitted preflight weights: 36
```

The fitted preflight used the accepted fixed recipe:

```text
optimizer: AdamW
learning rate: 0.0003
weight decay: 0.0001
global-norm clip: 1.0
max optimizer steps per profile: 128
seeds: 289800, 289801, 289802
continuous target loss: SmoothL1/Huber
binary target loss: BCE-with-logits for recoverability_window_success
normalization source: smoke_fit task_source_id split only
split unit: task_source_id
profile-specific tuning: false
target-family weight tuning: false
```

All six evaluator-only target families have at least one active scalar:

```text
future_braking_deceleration_envelope: 2 active scalars
future_yaw_authority: 2 active scalars
future_lateral_acceleration_response: 3 active scalars
actuator_response_lag_proxy: 3 active scalars
recovery_margin_after_maneuver: 2 active scalars
first_critical_action_quality: 1 active scalar
```

The accepted boundary facts remain:

```text
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
future target actor input required: false
evaluator targets actor visible: false
paper holdout admitted: false
preflight-only split: true
source-singleton rows paper proof allowed: false
guard rows ordinary success denominator allowed: false
fresh/source-diverse panel required before claim: true
```

M2898's smoke losses and fitted weights are useful for implementation
debugging, not for model-quality interpretation.

## Supported Claims

M2900 supports only these claims:

```text
The Route B capability-prediction chain is complete enough to support a
fresh/source-diverse panel expansion design.

The accepted implementation can fit the actor-safe L0/L1/L2/L3 profile heads
under the bounded M2896 recipe and preserve target visibility, split, rollback,
and claim boundaries.

The current bottleneck is no longer fitting implementation completeness; it is
the lack of a fresh/source-diverse evaluation or panel surface.

The next highest-leverage Route B action is a fresh/source-diverse panel design
that defines source diversity, holdout, target coverage, and materialization
criteria before model-quality work.
```

These are workflow and design-admission claims. They do not change driver
capability evidence and do not rank L0/L1/L2/L3 profiles.

## Falsified Claims

M2900 rejects these interpretations:

```text
M2898/M2899 validate prediction quality: false
M2898/M2899 rank controller families: false
M2898/M2899 select a finite-window or GRU winner: false
M2898/M2899 prove finite-window-vs-GRU outcome: false
M2898/M2899 prove current-response sufficiency: false
M2898/M2899 prove recurrent self-ID: false
M2898/M2899 prove driver performance: false
M2898/M2899 provide paper evidence or a current-sim verdict: false
M2898 fitted preflight weights are promoted checkpoints: false
M2901 may validate, rank, or claim model quality directly: false
```

The smoke_eval split in M2898 remains a leakage and wiring check only. It is
not a paper holdout and not a model-quality denominator.

## Failure Taxonomy Summary

Controlled or inactive after M2900:

```text
lineage_invalid:
  controlled by accepted M2890-M2899 parent chain and explicit artifacts.

contract_violation:
  controlled by actor 72/action 3, no hidden/oracle actor input,
  no future-target actor input, and evaluator-only targets actor-visible false.

metric_artifact:
  controlled at preflight level by recipe rows, normalization rows,
  availability rows, optimizer rows, diagnostics, rollback rows, and gate rows.

proof_washout:
  controlled by keeping source-singleton rows out of paper proof, guard rows
  out of ordinary denominators, and fitted preflight weights unpromoted.
```

Still active:

```text
scenario_sampling_failure:
  active because the usable Route B surface is still 17 public task rows.

objective_overfit:
  active because the fitting recipe has only public preflight rows and no
  fresh/source-diverse denominator.

seed_fragility:
  active until fresh/source-diverse rows or held-out seeds exist.

behavior_regression:
  active because Route B capability prediction is not closed-loop controller
  behavior evidence.

self_id_gap:
  active because no source-diverse history-necessity intervention or terminal
  boundary comparison has been run.

high_fidelity_dependency_gap:
  active because Route C/HF3 remains source-unavailable.
```

## Public Gate Overfit Risk

Public-gate overfit risk is high for any direct model-quality interpretation.

The accepted preflight chain is valuable because it is complete, bounded, and
machine-auditable. The same chain is risky because it can now produce fitted
weights and decreasing smoke losses over a small public panel. M2900 therefore
does not admit direct validation or ranking.

The next panel design must require:

```text
fresh task_source_id rows outside the existing 17 usable public rows
explicit source-family diversity accounting
max single-source share limits
target-family coverage accounting
separate fit, calibration, diagnostic, and later evaluation semantics
source-singleton rows as seeds or gaps only, not paper proof
guard rows outside ordinary denominators
paper holdout false unless a later manifest explicitly admits one
no actor-visible hidden dynamics, oracle labels, future targets, or verdicts
one materialization preflight before any model-quality design
```

Without that panel expansion, model-quality design would mostly formalize how
to measure on the same rows that already drove the implementation preflight.

## Admission Options

Option accepted:

```text
fresh/source-diverse capability-prediction panel design:
  accepted because the fitting implementation is complete but the current
  surface is too small and too public for quality measurement. A design
  milestone can define source-diversity, holdout, seed, target-coverage, and
  materialization criteria for a later new-panel preflight without running
  validation or making claims.
```

Options rejected for the immediate next action:

```text
direct model-quality design:
  rejected for now. Model-quality design is still needed later, but doing it
  before a fresh/source-diverse panel would keep the denominator anchored to
  public preflight rows and invite overfit.

direct validation, ranking, or winner selection:
  rejected. The accepted chain has only preflight smoke diagnostics and
  run-local fitted weights.

contract or implementation repair:
  rejected for the immediate next action because M2898/M2899 pass the required
  recipe, split, normalization, availability, optimizer, diagnostic, overfit,
  rollback, gate, and claim-boundary checks.

Route A pivot:
  rejected for the immediate next action because Route B now has a concrete
  evidence bottleneck and a bounded next action toward fresh panel evidence.
  Route A closed-loop behavior remains the ultimate engineering route but is
  not the blocker this synthesis is closing.

Route C pivot:
  rejected for the immediate next action because Chrono/HF3 remains stopped
  under source-unavailable. No supplied source or backend condition has changed.

stop:
  rejected because an actor-safe, bounded next design exists that can lead to
  new panel evidence rather than another public-row interpretation loop.
```

## Route Constraint Mapping

M2900 advances:

```text
workflow or complexity reduction: yes
scenario/task-quality evidence: no new evidence yet; admits fresh-panel design
engineering driver performance: no
mechanism evidence for history dependence: no
high-fidelity validation readiness: no
```

This remains consistent with `docs/self-id-go-no-go-paper-route-plan.md` and
`docs/paper-route-finite-window-vs-gru-plan.md`. Self-ID and GRU remain bounded
hypotheses, finite-window/current-response may still win, source-singleton
positives remain diagnostic only, and high-fidelity validation remains a later
Route C layer after current-sim evidence becomes interpretable.

## M2901 Admission Contract

M2901 is admitted as a bounded design gate:

```text
m2901-paper-route-l0-l1-l2-l3-capability-prediction-fresh-source-diverse-panel-design
```

M2901 must define:

```text
fresh/source-diverse panel scope and row taxonomy
source-family diversity criteria
max single-source share limits
minimum target-family coverage criteria
fit/calibration/diagnostic/evaluation split semantics
source-singleton rows as seed or gap rows only
guard-row exclusion semantics
actor and evaluator-target visibility boundaries
materialization artifact rows for the next preflight
rollback conditions for hidden/oracle or public-row leakage
one follow-up materialization manifest or stop decision
```

M2901 must not reset, step, roll out, replay, validate, fit additional weights,
train, run PPO, rank profiles, select a winner, promote a checkpoint, publish a
package, or claim model quality, driver performance, finite-window-vs-GRU
verdict, paper result, current-sim verdict, high-fidelity validation,
full-driver completion, or self-ID evidence.

## Next Branch Decision

M2900 continues Route B into a fresh-panel expansion branch:

```text
paper_route_l0_l1_l2_l3_capability_prediction_fresh_panel_expansion
```

The branch may continue only if M2901 produces a concrete design that can
admit a materialization preflight producing new dataset/panel evidence. If
M2901 cannot define a source-diverse panel without leaking hidden/oracle
information to actor input or reusing public rows as a quality denominator, it
must route to repair, Route A/C pivot, or stop.
