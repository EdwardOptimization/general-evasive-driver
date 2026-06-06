# M2886 Paper Route L0/L1/L2/L3 Capability-Prediction Panel Audit Synthesis Or Data Design

## Metadata

- status: completed
- decision: `admit_m2887_read_only_capability_prediction_dataset_materialization_over_17_usable_rows`
- manifest: `experiments/manifests/m2886-paper-route-l0-l1-l2-l3-capability-prediction-panel-audit-synthesis-or-data-design.json`
- design artifact: `docs/m2886-paper-route-l0-l1-l2-l3-capability-prediction-panel-audit-synthesis-or-data-design.md`
- parent audit: `docs/m2885-paper-route-l0-l1-l2-l3-capability-prediction-panel-inventory-result-audit.md`
- parent summary: `runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight/summary.json`
- parent candidate rows: `runs/m2884_paper_route_l0_l1_l2_l3_capability_prediction_panel_inventory_preflight/candidate_panel_rows.csv`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight.json`
- next: `m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight`

## Synthesis Decision

M2886 selects exactly one next action:

```text
read-only capability-prediction dataset materialization over the 17 M2884/M2885
usable rows
```

Formal decision:

```text
admit_m2887_read_only_capability_prediction_dataset_materialization_over_17_usable_rows
```

This is not training, not controller-family comparison, and not a paper or
self-ID verdict. It is the first bounded data materialization step after M2884
proved that the repo has a usable candidate inventory.

## Evidence Summary

M2884/M2885 provide the accepted inventory:

```text
candidate rows: 72
usable rows: 17
source-singleton rows: 34
guard rows: 21
target families: 6 evaluator-only families
actor contract: 72 observation / 3 action
hidden/oracle actor input required: false
evaluator targets actor visible: false
```

The 17 usable rows are split across the current Route B task families:

```text
T4 rows: 10
T5 rows: 7
```

Their environment-template coverage is:

```text
t4_actuator_delay_response: 5
t4_capability_step_temporal: 3
t4_staged_warmup_capability: 2
t5_boundary_axis_retarget: 5
t5_near_boundary_warmup: 2
```

The usable row pool is sufficient for a read-only dataset materialization
preflight because it covers both delayed/response and terminal-boundary route
families, has complete L0/L1/L2/L3 workload matrix coverage, and has
evaluator-only future-capability target columns. It is not sufficient for
training, ranking, or paper evidence by itself.

## Supported Claims

M2886 supports only this claim:

```text
The accepted M2884/M2885 inventory is sufficient to admit a read-only
capability-prediction dataset materialization over the 17 usable rows, while
keeping source-singleton and guard rows out of paper proof.
```

This can move Route B from inventory into dataset materialization. It still
does not answer whether L0, L1, L2, or L3 predicts future capability better.

## Falsified Or Rejected Claims

M2886 rejects these interpretations:

```text
the 17 usable rows are a benchmark: false
source-singleton rows can be paper proof: false
guard rows can enter ordinary success denominators: false
M2887 may train or rank controllers: false
M2887 may claim finite-window-vs-GRU verdict: false
M2887 may claim current-response sufficiency or recurrent self-ID: false
M2887 may expose future targets hidden dynamics or oracle labels to actor input: false
```

## Rejected Alternatives

M2886 rejects the other immediate next actions:

```text
fresh/source-diverse data-panel design first:
  rejected for the immediate next action because the 17 usable rows are enough
  to materialize and inspect the dataset contract before deciding whether more
  data is needed.

gate-utility audit:
  rejected for now because M2884 already separated 21 guard rows and the higher
  leverage step is to test whether usable rows can become an actor-safe
  capability-prediction dataset.

Route A pivot:
  rejected for now because Route B has a concrete accepted inventory and can
  produce a dataset artifact without training or changing actor inputs.

stop:
  rejected because M2884/M2885 found 17 usable rows and no actor-boundary
  blocker for read-only materialization.
```

## M2887 Admission Contract

M2887 is admitted as a bounded, read-only materialization preflight:

```text
m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight
```

M2887 must materialize a dataset contract from existing artifacts only. It must
not execute reset, step, rollout, replay, validation, training, PPO, ranking,
winner selection, promotion, package publication, or high-fidelity work.

Required output rows:

```text
summary.json
usable_task_rows.csv
profile_task_rows.csv
evaluator_target_rows.csv
excluded_source_singleton_rows.csv
excluded_guard_rows.csv
actor_feature_contract_rows.csv
dataset_gate_rows.csv
claim_rows.csv
follow-up result-audit manifest
```

The `profile_task_rows.csv` should have one row per usable task-source id and
controller-family profile. With the current 17 usable rows and 12 required
profiles, the expected profile-task row count is:

```text
17 * 12 = 204
```

The materialized rows may include evaluator-only target values or target
availability flags, but those fields must be marked actor-invisible.

## Failure Taxonomy

Controlled by this design:

```text
lineage_invalid: controlled by using M2884/M2885 accepted inventory only
contract_violation: controlled by actor 72/action 3 and evaluator-only target boundary
proof_washout: controlled by excluding 34 source-singleton rows and 21 guard rows from proof
metric_artifact: controlled by materializing target availability before modeling
```

Still active:

```text
scenario_sampling_failure: active because the first dataset uses only 17 usable rows
objective_overfit: active if later modeling tunes only to these public rows
self_id_gap: active because no history-necessity or intervention comparison exists
behavior_regression: active because recent Route A closed-loop diagnostics remain weak
high_fidelity_dependency_gap: active because Route C/HF3 remains source-unavailable
```

## Public Gate Overfit Risk

Public-gate overfit risk remains medium. M2887 may materialize only the 17
accepted usable rows, but it must not optimize or train against them. The next
audit must decide whether the materialized dataset is sufficient for a
capability-prediction implementation, whether source-singleton coverage forces
a fresh data-panel design, or whether this branch needs synthesis.

## Next Route

M2886 registers:

```text
m2887-paper-route-l0-l1-l2-l3-capability-prediction-dataset-materialization-preflight
```

M2887 must preserve the non-negotiable actor contract and the paper-route
claim ladder. It may only materialize actor-safe dataset rows and evaluator
labels; it must not run or claim a model comparison.
