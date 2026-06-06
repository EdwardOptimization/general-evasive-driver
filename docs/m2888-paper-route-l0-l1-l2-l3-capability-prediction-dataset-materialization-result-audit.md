# M2888 Paper Route L0/L1/L2/L3 Capability-Prediction Dataset Materialization Result Audit

## Metadata

- status: completed
- decision: `accept_m2887_dataset_materialization_claim_safe_route_to_m2889_synthesis_or_modeling_design`
- manifest: `experiments/manifests/m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit.json`
- audit artifact: `docs/m2888-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-result-audit.md`
- parent summary: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/summary.json`
- parent usable rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/usable_task_rows.csv`
- parent profile-task rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/profile_task_rows.csv`
- parent gate rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/dataset_gate_rows.csv`
- parent claim rows: `runs/m2887_paper_route_l0_l1_l2_l3_capability_prediction_dataset_materialization_preflight/claim_rows.csv`
- follow-up manifest: `experiments/manifests/m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design.json`
- next: `m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design`

## Audit Decision

M2888 accepts M2887 as a complete and claim-safe read-only Route B
capability-prediction dataset materialization.

Decision:

```text
accept_m2887_dataset_materialization_claim_safe_route_to_m2889_synthesis_or_modeling_design
```

This acceptance is narrow. M2887 materializes a dataset contract for later
capability-prediction work. It does not train a model, rank controller
families, compare finite-window against GRU, validate driver performance, or
prove self-identification.

M2889 must synthesize this accepted materialization before any modeling
implementation or training is admitted.

## Artifact Completeness

M2887 wrote all required artifacts and passed its gate matrix:

```text
status_pass: true
gate_matrix_pass: true
candidate panel rows read: 72
usable task rows: 17
profile-task rows: 204
evaluator-only target rows: 6
source-singleton exclusion rows: 34
guard exclusion rows: 21
actor-feature contract rows: 5
dataset gate rows: 9
claim rows: 12
follow-up manifest exists: true
```

The profile-task matrix is complete for the required 12 profiles:

```text
L0 rows: 17
L1 rows: 17
L2 rows: 136
L3 rows: 34
total: 204
```

No dataset repair is required before M2889.

## Dataset Reading

The accepted materialized rows remain bounded:

```text
usable task rows: 17
task family split: T4 10 / T5 7
environment-template split:
  t4_actuator_delay_response: 5
  t4_capability_step_temporal: 3
  t4_staged_warmup_capability: 2
  t5_boundary_axis_retarget: 5
  t5_near_boundary_warmup: 2
```

This coverage is enough to support a modeling-design decision. It is not
enough by itself to support paper proof, controller-family ranking, or a
current-sim verdict.

## Boundary Audit

M2887 preserved the actor and target boundaries:

```text
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
evaluator targets actor visible: false
source-singleton rows paper proof allowed: false
guard rows ordinary success denominator allowed: false
```

The six future-capability target families remain evaluator-only:

```text
future braking deceleration envelope
future yaw authority
future lateral acceleration response
actuator response lag proxy
recovery margin after maneuver
first-critical action quality
```

They may be used later as prediction labels or audit targets, but not as actor
inputs or policy-side route answers.

## Supported Claims

M2888 supports only these claims:

```text
M2887 materialized a complete dataset contract over 17 accepted usable rows.
M2887 materialized the expected 204 profile-task rows.
M2887 preserved 34 source-singleton and 21 guard exclusions.
M2887 preserved actor 72/action 3 and evaluator-only target boundaries.
M2887 registered a bounded M2888 audit handoff.
```

These are process and dataset-contract claims, not driver capability claims.

## Rejected Interpretations

M2888 rejects these interpretations:

```text
M2887 validates driver performance: false
M2887 ranks controller families: false
M2887 proves finite-window-vs-GRU outcome: false
M2887 proves current-response sufficiency: false
M2887 proves recurrent self-ID: false
M2887 proves current-sim verdict: false
M2887 proves high-fidelity validation readiness/result: false
M2887 selects a winner or promotes a checkpoint: false
M2887 permits actor-visible future targets or oracle labels: false
```

M2888 also accepts the M2887 false-claim flags: no reset, step, rollout,
replay, validation, training, PPO, ranking, winner selection, checkpoint
promotion, package publication, driver-performance claim, paper claim,
finite-window-vs-GRU claim, current-sim claim, high-fidelity claim,
full-driver claim, or self-ID claim was made.

## Failure Taxonomy

Controlled or inactive after audit:

```text
lineage_invalid: controlled by M2884/M2885/M2886/M1690 lineage and M2887 gates
contract_violation: controlled by actor 72/action 3 and evaluator-only targets
metric_artifact: controlled by row-count gates and explicit target/exclusion rows
proof_washout: controlled by source-singleton and guard exclusions
```

Still active:

```text
scenario_sampling_failure: active because the first materialized contract has only 17 usable rows
objective_overfit: active if later modeling optimizes only the public 17 rows
behavior_regression: active because recent Route A closed-loop diagnostics remain weak
self_id_gap: active because no history-necessity or intervention comparison exists
high_fidelity_dependency_gap: active because Route C/HF3 remains source-unavailable
```

## Public Gate Overfit Risk

Public-gate overfit risk remains medium. M2887 is useful because it provides a
machine-auditable dataset contract, but the materialized rows are still the
accepted public rows from existing artifacts. They must not become the sole
training objective or ordinary benchmark denominator.

M2889 must decide whether to:

```text
admit a bounded capability-prediction modeling design over this dataset contract
first design a fresh/source-diverse data-panel expansion
repair or expand dataset gates if modeling would be under-specified
pivot to Route A or Route C if Route B is not the highest-leverage step
stop the branch if the dataset contract is insufficient
```

## Next Route

M2888 registers this bounded follow-up:

```text
m2889-paper-route-l0-l1-l2-l3-capability-prediction-materialization-audit-synthesis-or-modeling-design
```

M2889 must choose exactly one next action before any capability-prediction
implementation, environment execution, training, validation, ranking,
promotion, paper verdict, current-sim verdict, high-fidelity validation, or
self-ID claim is admitted.
