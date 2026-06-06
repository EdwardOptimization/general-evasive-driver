# M2895 Paper Route L0/L1/L2/L3 Capability-Prediction Implementation Branch Synthesis

## Metadata

- status: completed
- synthesis decision: `continue`
- next branch decision: `continue_admit_m2896_bounded_capability_prediction_fitting_design`
- manifest: `experiments/manifests/m2895-paper-route-l0-l1-l2-l3-capability-prediction-implementation-branch-synthesis.json`
- synthesis artifact: `docs/m2895-paper-route-l0-l1-l2-l3-capability-prediction-implementation-branch-synthesis.md`
- parent audit: `docs/m2894-paper-route-l0-l1-l2-l3-capability-prediction-implementation-result-audit.md`
- parent implementation summary: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/summary.json`
- parent modeling-contract audit: `docs/m2892-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-materialization-result-audit.md`
- parent modeling-contract summary: `runs/m2891_paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight/summary.json`
- parent design: `docs/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.md`
- prior synthesis: `docs/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.md`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.json`
- next: `m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design`

## Synthesis Decision

M2895 selects exactly one next action:

```text
admit a bounded capability-prediction fitting design
```

Formal decision:

```text
continue_admit_m2896_bounded_capability_prediction_fitting_design
```

This is a Route B continuation, not a fitting or training result. M2896 may
design a split-aware, actor-safe fitting recipe and audit ladder for the
capability-prediction model family. It must not run optimizer steps, persist
fitted weights, validate prediction quality, rank controller families, select a
winner, promote a checkpoint, or claim finite-window-vs-GRU, current-sim,
paper, high-fidelity, full-driver, driver-performance, model-quality, or self-ID
evidence.

## Evidence Summary

M2890-M2894 provide a complete and claim-safe implementation-preflight chain:

```text
M2890 modeling-contract design: completed
M2891 modeling-contract materialization: completed
M2892 modeling-contract materialization audit: completed
M2893 implementation preflight: completed
M2894 implementation result audit: completed
```

Accepted dataset and modeling-contract facts:

```text
usable task rows: 17
profile-task rows: 204
required profiles: 12
L0 rows: 17
L1 rows: 17
L2 rows: 136
L3 rows: 34
feature contract rows: 12
label contract rows: 6
split contract rows: 8
loss/metric contract rows: 6
baseline contract rows: 12
modeling gate rows: 13
modeling claim rows: 14
source-singleton exclusion rows: 34
guard exclusion rows: 21
```

Accepted implementation-preflight facts:

```text
status_pass: true
gate_matrix_pass: true
schema rows: 18
loader smoke rows: 12
loader smoke rows all pass: true
model-head smoke rows: 12
model-head smoke rows all pass: true
gate rows: 9
claim rows: 17
target families: 6
target scalar dimension: 19
required profiles: 12
paper_holdout_admitted: false
preflight_only_split: true
```

Actor and target boundaries remain preserved:

```text
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
future target actor input required: false
evaluator targets actor visible: false
source-singleton rows paper proof allowed: false
guard rows ordinary success denominator allowed: false
```

The 12 profile names remain the governing comparison surface:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L2_window_50
L2_window_50_current_tiled
L2_window_100
L2_window_100_current_tiled
L3_online_gru
L3_reset_control_corrected
```

The six evaluator-only target families remain actor-invisible:

```text
future_braking_deceleration_envelope
future_yaw_authority
future_lateral_acceleration_response
actuator_response_lag_proxy
recovery_margin_after_maneuver
first_critical_action_quality
```

M2895 interprets the chain as sufficient for fitting-design admission. It is
not sufficient for direct fitting, training, model validation, paper evidence,
or controller-family verdicts.

## Supported Claims

M2895 supports only these claims:

```text
M2890-M2894 define a complete actor-safe capability-prediction preflight chain.
The chain covers L0/L1/L2/L3 profile semantics, evaluator-only target families,
split semantics, losses, metrics, baselines, schema rows, loader smoke rows,
and model-head shape smoke rows.
The chain preserves actor 72/action 3 and no hidden/oracle or future-target
actor input.
The next highest-leverage action is a bounded fitting-design milestone that
turns the preflight chain into explicit optimizer, split, mask, overfit guard,
rollback, and audit requirements before any actual fitting.
```

These are workflow and design-admission claims. They do not change driver
capability evidence.

## Falsified Claims

M2895 rejects these interpretations:

```text
M2890-M2894 fit or train a capability-prediction model: false
M2890-M2894 validate prediction quality: false
M2890-M2894 rank L0/L1/L2/L3 profiles: false
M2890-M2894 prove finite-window-vs-GRU outcome: false
M2890-M2894 prove current-response sufficiency: false
M2890-M2894 prove recurrent self-ID: false
M2890-M2894 prove driver performance: false
M2890-M2894 provide paper evidence or a current-sim verdict: false
M2890-M2894 prove high-fidelity validation readiness/result: false
M2890-M2894 select a winner or promote a checkpoint: false
M2896 may run optimizer steps or persist fitted weights: false
```

M2895 also rejects direct implementation training from M2894. The next
milestone must first define the fitting recipe, not execute it.

## Failure Taxonomy Summary

Controlled or inactive after M2895:

```text
lineage_invalid:
  controlled by accepted M2889-M2894 lineage and explicit parent artifacts.

contract_violation:
  controlled by actor 72/action 3, hidden/oracle false, future-target actor
  input false, and evaluator-only targets actor-visible false.

metric_artifact:
  controlled at preflight level by explicit loss/metric rows, target masks,
  model-head smoke rows, and no model-quality interpretation.

proof_washout:
  controlled by preserving 34 source-singleton and 21 guard exclusions outside
  paper proof and ordinary denominators.
```

Still active:

```text
scenario_sampling_failure:
  active because the usable public surface has only 17 task rows.

objective_overfit:
  active because fitting could over-optimize the small public preflight surface.

seed_fragility:
  active until any later fitting design specifies seed handling and disjoint
  evaluation surfaces.

behavior_regression:
  active because Route B preflight has not produced new closed-loop driver
  behavior evidence.

self_id_gap:
  active because no history-necessity intervention comparison has been run.

high_fidelity_dependency_gap:
  active because Route C/HF3 remains source-unavailable.
```

M2896 must address the active fitting risks before implementation. It should
not hide them by labeling the 17 rows as a benchmark.

## Public Gate Overfit Risk

Public-gate overfit risk is medium to high.

The implementation chain is valuable because it is complete, actor-safe, and
machine-checkable. The same chain is risky because it is built over a small,
public, preflight-only surface:

```text
usable task rows: 17
source-singleton exclusions: 34
guard exclusions: 21
paper holdout: not admitted
split semantics: preflight-only
```

M2896 is admitted only if it treats this as a design constraint. Its fitting
recipe must define:

```text
task_source_id-level split isolation
availability-mask loss semantics
no source-singleton or guard proof rows
no paper holdout claim
seed and bootstrap discipline for smoke-only fitting
fresh/source-diverse panel trigger before paper or ranking claims
rollback if hidden/oracle or future labels enter actor input
rollback if loss improves only on public preflight rows
one result-audit handoff before implementation
```

The immediate route is therefore a fitting design, not a fitting run.

## Admission Options

Option accepted:

```text
bounded capability-prediction fitting design:
  accepted because M2890-M2894 have completed the design, materialization,
  audit, implementation-preflight, and audit ladder required before fitting can
  even be specified. A design milestone can now define optimizer, masking,
  split, seed, overfit, rollback, and audit rules without changing weights or
  making model-quality claims.
```

Options rejected for the immediate next action:

```text
direct fitting or training implementation:
  rejected. The branch has only smoke-level implementation evidence and no
  explicit fitting recipe, optimizer boundary, rollback plan, or audit gate.

fresh/source-diverse data-panel design:
  deferred. The 17-row surface is too small for paper proof, but a fitting
  design is still useful because it can define exactly what fresh/source-diverse
  panel gates a later implementation or paper claim must satisfy.

contract or implementation repair:
  rejected for the immediate next action because M2891-M2894 pass the required
  row-count, actor-boundary, target-visibility, schema, loader, model-head, gate,
  and claim checks.

Route A pivot:
  rejected for the immediate next action because Route B now has a complete
  implementation-preflight chain and a low-cost design action. Route A closed
  loop behavior evidence remains active but is not the current highest-leverage
  blocker for the paper route.

Route C pivot:
  rejected for the immediate next action because Chrono/HF3 remains stopped
  under source-unavailable. No supplied source or backend condition has changed.

stop:
  rejected because an actor-safe, bounded, evidence-producing design step
  exists.
```

## Route Constraint Mapping

M2895 advances:

```text
workflow or complexity reduction: yes
scenario/task-quality evidence: no
engineering driver performance: no
mechanism evidence for history dependence: no
high-fidelity validation readiness: no
```

This is consistent with `docs/self-id-go-no-go-paper-route-plan.md` and
`docs/paper-route-finite-window-vs-gru-plan.md`: self-ID remains falsifiable,
finite-window/current-response may still win, GRU is not assumed as the final
controller, and high-fidelity validation remains a later Route C layer after
current-sim evidence is interpretable.

## Next Branch Decision

M2895 registers this bounded follow-up:

```text
m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design
```

M2896 must define a fitting recipe and audit ladder only. It must specify
allowed optimizer scope, target masks, split units, seed discipline, baseline
reporting, overfit triggers, fresh-panel triggers, rollback conditions, and one
follow-up result-audit manifest. It must not reset, step, roll out, replay, run
optimizer steps, fit weights, train, validate, rank, promote, publish, select a
winner, claim prediction quality, claim driver performance, claim
finite-window-vs-GRU evidence, claim paper evidence, claim current-sim or
high-fidelity verdicts, claim full-driver completion, or claim self-ID evidence.
