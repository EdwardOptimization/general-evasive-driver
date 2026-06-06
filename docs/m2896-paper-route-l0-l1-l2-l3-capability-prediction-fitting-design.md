# M2896 Paper Route L0/L1/L2/L3 Capability-Prediction Fitting Design

## Metadata

- status: completed
- decision: `admit_m2897_capability_prediction_fitting_design_result_audit`
- manifest: `experiments/manifests/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.json`
- design artifact: `docs/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.md`
- parent synthesis: `docs/m2895-paper-route-l0-l1-l2-l3-capability-prediction-implementation-branch-synthesis.md`
- parent audit: `docs/m2894-paper-route-l0-l1-l2-l3-capability-prediction-implementation-result-audit.md`
- parent implementation summary: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/summary.json`
- parent schema rows: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/schema_rows.csv`
- parent loader smoke rows: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/loader_smoke_rows.csv`
- parent model-head smoke rows: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/model_head_smoke_rows.csv`
- parent modeling-contract summary: `runs/m2891_paper_route_l0_l1_l2_l3_capability_prediction_modeling_contract_materialization_preflight/summary.json`
- paper route plan: `docs/self-id-go-no-go-paper-route-plan.md`
- finite-window route plan: `docs/paper-route-finite-window-vs-gru-plan.md`
- follow-up manifest: `experiments/manifests/m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit.json`
- next: `m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit`

## Design Decision

M2896 admits a bounded result audit of this capability-prediction fitting
design. It does not admit direct optimizer execution.

Formal decision:

```text
admit_m2897_capability_prediction_fitting_design_result_audit
```

If M2897 accepts this design, the next implementation preflight may implement a
small, deterministic fitting smoke over the accepted M2893 schema and loader
surface. That later preflight may produce fitted preflight weights only as
auditable implementation artifacts. It must not rank profiles, select a winner,
promote weights, claim model quality, claim paper evidence, or claim
finite-window-vs-GRU/self-ID evidence.

M2896 itself does not reset, step, roll out, replay, fit, train, run PPO, run
optimizer steps, persist fitted weights, validate, rank, select a winner,
promote a checkpoint, publish a package, or claim prediction quality, driver
performance, paper evidence, current-sim verdict, high-fidelity validation,
full-driver completion, or level3 self-identification.

## Evidence Used

M2895 accepted the M2890-M2894 implementation-preflight chain as complete
enough for fitting-design admission only:

```text
usable task rows: 17
profile-task rows: 204
source-singleton exclusions: 34
guard exclusions: 21
schema rows: 18
loader smoke rows: 12
model-head smoke rows: 12
target families: 6
target scalar dimension: 19
required profiles: 12
paper holdout admitted: false
preflight-only split: true
```

Actor and target boundaries remain non-negotiable:

```text
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
future target actor input required: false
evaluator targets actor visible: false
source-singleton rows paper proof allowed: false
guard rows ordinary success denominator allowed: false
```

M2893 model-head smoke materialized only shape contracts:

```text
L0/L1 input shape: batch,obs=72
L2 input shape: batch,window={13,25,50,100},obs=72
L3 input shape: batch,obs=72; hidden=actor_internal
output shape: batch,target_dim=19
optimizer_step_run: false
fitted_weights_persisted: false
training_scheduled: false
validation_scheduled: false
```

M2896 uses this as recipe-design evidence. It does not convert smoke rows into
model-quality evidence.

## Route Boundary

This remains Route B paper-evidence preparation under
`docs/post-m2470-route-plan.md`, `docs/self-id-go-no-go-paper-route-plan.md`,
and `docs/paper-route-finite-window-vs-gru-plan.md`.

Allowed interpretation:

```text
an actor-safe capability-prediction fitting recipe can now be specified for a
later preflight
```

Forbidden interpretation:

```text
prediction quality
driver performance
controller-family ranking
finite-window-vs-GRU verdict
current-response sufficiency
recurrent self-ID
paper evidence
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
checkpoint promotion
```

## Fitting Objective Contract

A later implementation preflight, only after M2897 accepts this design, may
use this bounded objective:

```text
loss_capability =
  sum_{profile,batch,target}(availability_mask * target_family_weight *
      per_target_loss(predicted_target - normalized_target))
  / max(epsilon, sum_{profile,batch,target}(availability_mask * target_family_weight))
```

Required loss details:

```text
continuous targets:
  SmoothL1/Huber regression over train-split robust-normalized target columns

binary recoverability target:
  BCE-with-logits only for explicitly binary availability-masked entries

availability mask:
  required for every target scalar and profile row

target_family_weight:
  fixed to 1.0 for all target families in the first implementation preflight

loss-mass normalization:
  required so missing targets do not silently change objective scale

non-finite target or prediction:
  hard failure, not imputation
```

No target family may be upweighted after observing profile metrics. If a later
preflight needs target-family weights, it must route through a separate design
or audit milestone.

## Target Normalization And Masks

Normalization must be train-split only:

```text
normalization statistic: robust median and IQR or MAD per target scalar
statistic source: train task_source_id split only
minimum finite entries: 2 per scalar for smoke; otherwise mark scalar masked
IQR/MAD floor: positive epsilon to avoid divide by zero
eval/smoke split usage: apply train statistics only
paper holdout usage: forbidden, not admitted
```

Mask rules:

```text
missing required scalar:
  target scalar unavailable and excluded from loss

missing required target family:
  fail closed for that target family and route to audit/repair

non-finite normalized value:
  fail the row

binary recoverability unavailable:
  mask binary loss for that row

masked scalar:
  may be reported as availability, not as zero target
```

The implementation preflight must write target-normalization and
availability-mask audit rows before any optimizer step.

## Split Contract

The split unit is `task_source_id`, never `profile_task_id`.

Fixed first fitting-smoke split policy:

```text
split name: public_preflight_task_source_split
split unit: task_source_id
profile leakage across split: forbidden
all profiles for one task_source_id: assigned to the same split
paper holdout admitted: false
ordinary validation denominator: false
ranking allowed: false
winner selection allowed: false
```

Deterministic split assignment:

```text
sort task_source_id lexicographically
assign every fifth task_source_id to smoke_eval
assign remaining task_source_id values to smoke_fit
if smoke_eval would be empty, fail closed
if any profile for a task_source_id crosses split, fail closed
```

The split is a software and leakage check only. It is not a validation result
or paper holdout.

## Optimizer Scope

Only a later implementation preflight may run optimizer steps, and only if
M2897 accepts this design. The allowed first implementation scope is:

```text
optimizer: AdamW
learning rate: 0.0003
weight decay: 0.0001
max optimizer steps per profile: 128
batching: deterministic full-batch or deterministic mini-batch with fixed seed
seed list: 289800, 289801, 289802
gradient clipping: global norm 1.0
early stopping: disabled for the first smoke
profile-specific tuning: forbidden
target-family weight tuning: forbidden
checkpoint promotion: forbidden
winner selection: forbidden
```

All 12 profiles must use the same optimizer recipe and target vector. The
implementation preflight may report diagnostics per profile, but those
diagnostics must not rank profiles or decide finite-window-vs-GRU outcome.

## Model Family Contract

The first implementation preflight must preserve the M2893 model-head shape
families:

```text
L0_current_masked:
  MLP readout over current deployable observation only.

L1_one_step:
  MLP readout over current deployable observation plus previous-command and
  actuator-state feature family as already materialized.

L2_window_13 / 25 / 50 / 100:
  temporal pool or flatten shape contract over deployable command-response
  windows only.

L2_window_*_current_tiled:
  identical capacity/control baseline with current frame tiled, not history
  evidence.

L3_online_gru:
  recurrent readout shape contract over actor-internal recurrent state.

L3_reset_control_corrected:
  reset/truncation control, not a weaker training budget.
```

Parameter counts, input shapes, and inference-cost proxies must be reported
for each profile before any later model-quality interpretation. M2896 does not
claim that any architecture is better.

## Baseline Reporting

The later implementation preflight must include these baselines:

```text
train-split target median baseline
train-split zero-normalized baseline
current-tiled L2 controls for every L2 window
L3 reset/truncation control
parameter-count and inference-cost rows
```

Baseline diagnostics are allowed only to detect implementation failures. They
must not become ranking, winner selection, paper, or finite-window-vs-GRU
claims.

## Public-Row Overfit Guards

The 17 usable rows remain a public preflight surface. The fitting recipe must
therefore fail closed or route away if any of these happen:

```text
fit loss improves while smoke_eval loss is non-finite
fit loss improves only for one profile family and the same recipe is not used
smoke_eval task_source_id leakage is detected
source-singleton or guard rows enter fit/eval denominators
paper holdout is claimed or implied
target family weights are adjusted after observing diagnostics
profile metrics are used to rank L0/L1/L2/L3
```

Before paper claims, a later route must add a fresh/source-diverse panel or
explicitly synthesize why the paper route should stop. M2896 does not admit
paper proof from the current public rows.

## Rollback And Audit Gates

Proof gates for a later implementation preflight:

```text
actor observation/action contract unchanged
hidden/oracle actor input false
future target actor input false
evaluator targets actor visible false
all 12 profiles use the same optimizer recipe
target-normalization rows written before optimizer step
availability-mask rows written before optimizer step
task_source_id split rows written before optimizer step
source-singleton and guard rows excluded
optimizer steps bounded by design
fitted weights marked preflight-only and not promoted
```

Generalization gates:

```text
not admitted by M2896
fresh/source-diverse panel trigger must remain active
paper holdout remains false
```

Rollback gates:

```text
rollback if actor input shape changes
rollback if hidden/oracle or future target fields become actor-visible
rollback if task_source_id split leakage occurs
rollback if loss uses unavailable targets as zeros
rollback if optimizer step budget differs by profile
rollback if profile-specific tuning occurs
rollback if source-singleton or guard rows enter proof or denominators
rollback if any result is interpreted as model quality or ranking
```

Promotion gates:

```text
not admitted
checkpoint_promoted=false
winner_selected=false
ranking_run=false
model_quality_claim_made=false
paper_claim_made=false
```

## Required Implementation-Preflight Artifacts

If M2897 accepts this design and admits an implementation preflight, that
preflight must write at least:

```text
summary.json
fitting_recipe_rows.csv
task_source_split_rows.csv
target_normalization_rows.csv
availability_mask_rows.csv
optimizer_step_rows.csv
profile_metric_diagnostic_rows.csv
baseline_diagnostic_rows.csv
overfit_guard_rows.csv
rollback_rows.csv
claim_rows.csv
follow-up result-audit manifest
```

The summary must explicitly report:

```text
optimizer_step_run
fitted_weights_persisted
training_run
validation_run
ranking_run
model_quality_claim_made
paper_claim_made
finite_window_vs_gru_claim_made
level3_self_id_claim_made
```

Any true value must be allowed by the accepted implementation-preflight
manifest and remain preflight-only. M2896 does not allow promotion or paper
interpretation.

## Follow-Up Route

M2896 registers:

```text
m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit
```

M2897 must audit this design before any implementation preflight. It should
accept the route only if optimizer scope, split isolation, target masks,
normalization, baselines, public-row overfit guards, rollback criteria, and
claim boundaries are complete and actor-safe. If accepted, M2897 may admit one
bounded implementation preflight. If rejected, it must route to contract repair,
fresh/source-diverse data-panel design, Route A/Route C pivot, or stop.
