# M2889 Paper Route L0/L1/L2/L3 Capability-Prediction Materialization Audit Synthesis Or Modeling Design

## Metadata

- status: completed
- decision: `continue_admit_m2890_bounded_capability_prediction_modeling_contract_design`
- manifest: `experiments/manifests/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.json`
- synthesis artifact: `docs/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.md`
- parent audit: `docs/m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit.md`
- parent summary: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/summary.json`
- parent profile-task rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/profile_task_rows.csv`
- parent evaluator targets: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/evaluator_target_rows.csv`
- parent actor contract: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/actor_feature_contract_rows.csv`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- route split plan: `docs/post-m2470-route-plan.md`
- follow-up manifest: `experiments/manifests/m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design.json`
- next: `m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design`

## Synthesis Decision

M2889 selects exactly one next action:

```text
admit a bounded capability-prediction modeling contract design
```

Formal decision:

```text
continue_admit_m2890_bounded_capability_prediction_modeling_contract_design
```

This is a Route B continuation, not a training or model-implementation result.
The next milestone may design the actor-safe feature, target, split, loss,
baseline, and gate contract for capability prediction. It must not fit a model,
rank controller families, select a winner, promote a checkpoint, or claim
finite-window-vs-GRU, current-sim, paper, high-fidelity, full-driver, or self-ID
evidence.

## Evidence Summary

M2887/M2888 provide a complete and claim-safe dataset contract:

```text
status_pass: true
gate_matrix_pass: true
candidate panel rows read: 72
usable task rows: 17
profile-task rows: 204
required profiles: 12
evaluator-only target rows: 6
source-singleton exclusion rows: 34
guard exclusion rows: 21
actor-feature contract rows: 5
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
evaluator targets actor visible: false
```

The profile-task matrix covers the intended L0/L1/L2/L3 comparison surface:

```text
L0 rows: 17
L1 rows: 17
L2 rows: 136
L3 rows: 34
total profile-task rows: 204
```

The accepted usable task rows cover the current Route B T4/T5 focus:

```text
T4 rows: 10
T5 rows: 7
t4_actuator_delay_response: 5
t4_capability_step_temporal: 3
t4_staged_warmup_capability: 2
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 2
```

The six evaluator-only target families are available for modeling-contract
design:

```text
future_braking_deceleration_envelope
future_yaw_authority
future_lateral_acceleration_response
actuator_response_lag_proxy
recovery_margin_after_maneuver
first_critical_action_quality
```

This evidence is sufficient to design a bounded capability-prediction modeling
contract. It is not sufficient to train, evaluate, rank, or claim a controller
family result.

## Supported Claims

M2889 supports only these claims:

```text
M2887/M2888 define a complete actor-safe dataset contract for Route B
capability-prediction design.
The contract includes L0/L1/L2/L3 profile-task rows and evaluator-only future
capability targets.
The next highest-leverage action is a modeling-contract design that defines
features, labels, splits, losses, baselines, gates, and audit handoff before
implementation.
```

The supported claim is workflow and design admission. It does not change driver
capability evidence.

## Falsified Claims

M2889 rejects these interpretations:

```text
M2887/M2888 prove driver performance: false
M2887/M2888 rank L0/L1/L2/L3 controller families: false
M2887/M2888 prove finite-window-vs-GRU verdict: false
M2887/M2888 prove current-response sufficiency: false
M2887/M2888 prove recurrent self-ID: false
M2887/M2888 prove a current-sim verdict: false
M2887/M2888 prove high-fidelity validation readiness/result: false
M2887/M2888 permit actor-visible future targets or oracle labels: false
M2890 may train or fit a model: false
```

The 17 usable rows and 204 profile-task rows are a contract surface, not a
paper denominator or performance benchmark.

## Failure Taxonomy Summary

Controlled by M2889:

```text
lineage_invalid: controlled by accepting only the M2887/M2888 audited dataset
contract_violation: controlled by actor 72/action 3 and actor-invisible targets
proof_washout: controlled by preserving 34 source-singleton and 21 guard
exclusions
metric_artifact: controlled by requiring target, split, loss, and gate design
before implementation
```

Still active:

```text
scenario_sampling_failure: active because the contract has only 17 usable rows
objective_overfit: active if later fitting optimizes the public contract rows
seed_fragility: active until fresh/source-diverse rows or held-out seeds exist
behavior_regression: active because Route B design does not prove closed-loop
driver behavior
self_id_gap: active because no history-necessity intervention has been run
high_fidelity_dependency_gap: active because Route C/HF3 remains source
unavailable
```

## Public Gate Overfit Risk

Public-gate overfit risk remains medium.

The existing contract is useful because it is complete, actor-safe, and
machine-auditable. The risk is that later work could overfit the fixed 17
public usable rows or treat the excluded source-singleton rows as paper proof.
M2890 must therefore stay at modeling-contract design level and require:

```text
no model fitting
no controller ranking
no paper denominator from source-singleton or guard rows
explicit train/eval/holdout split semantics before implementation
target visibility checks before any data loader or model code
baseline definitions for L0/L1/L2/L3 and current-tiled controls
failure triggers for under-specified targets or too-small split coverage
```

The accepted next action reduces workflow ambiguity without converting public
rows into a performance claim.

## Admission Options

Option accepted:

```text
capability-prediction modeling contract design:
  accepted because M2887/M2888 already provide complete target, profile, and
  actor-boundary artifacts. Designing the contract is the shortest route to an
  implementable, actor-safe capability predictor while preserving claim
  boundaries.
```

Options rejected for the immediate next action:

```text
fresh/source-diverse data-panel design:
  rejected for this step because the existing contract can first define what
  source diversity, split semantics, and utility gates a later expansion must
  satisfy. Fresh data remains a likely follow-up if M2890 finds the design is
  underpowered.

dataset repair or utility audit:
  rejected for this step because M2887/M2888 passed row-count, target, actor,
  and exclusion gates. Utility checks should be part of the M2890 contract
  design rather than a separate repair-only loop now.

Route A pivot:
  rejected for this step because Route B has a complete dataset contract and a
  low-cost modeling-design action. Route A closed-loop weakness remains active
  but is not the highest-leverage immediate use of the accepted M2887/M2888
  artifacts.

Route C pivot:
  rejected for this step because the latest Chrono/HF3 route remains stopped
  under source-unavailable. No new external source or backend condition has
  changed.

stop:
  rejected because an actor-safe, evidence-producing design step exists.
```

## Route Constraint Mapping

M2889 advances:

```text
workflow or complexity reduction: yes
scenario/task-quality evidence: weak design admission only
engineering driver performance: no
mechanism evidence for history dependence: no
high-fidelity validation readiness: no
```

This is consistent with the paper-route plans: self-ID remains falsifiable,
finite-window/current-response may still win, and GRU is not assumed as the
final controller.

## M2890 Admission Contract

M2890 is admitted as a bounded design gate:

```text
m2890-paper-route-l0-l1-l2-l3-capability-prediction-modeling-contract-design
```

M2890 must define:

```text
actor-safe input feature contract
evaluator-only label contract
target normalization and missing-value policy
train/eval/holdout split semantics
L0/L1/L2/L3 and current-tiled baseline definitions
loss and metric families
gate rows required before implementation
claim boundaries and stop conditions
at most one follow-up implementation, fresh-data, repair, pivot, or stop
manifest
```

M2890 must not reset, step, roll out, replay, validate, train, fit a model,
run PPO, rank controller families, select a winner, promote a checkpoint,
publish a package, or claim driver performance, finite-window-vs-GRU verdict,
paper result, current-sim verdict, high-fidelity validation, full-driver
completion, or self-ID evidence.

## Next Branch Decision

M2889 continues Route B into a new modeling-contract design branch:

```text
paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract
```

The branch may continue only if M2890 produces a concrete actor-safe modeling
contract and preserves the source-singleton, guard, and evaluator-only target
boundaries. If M2890 cannot define fair split/target/loss/gate semantics for
the 17-row contract, it must route to fresh/source-diverse panel design,
dataset repair/utility audit, Route A/C pivot, or stop rather than starting
model implementation by inertia.
