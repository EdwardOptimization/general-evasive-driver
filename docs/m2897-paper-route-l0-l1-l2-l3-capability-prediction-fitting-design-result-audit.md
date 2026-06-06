# M2897 Paper Route L0/L1/L2/L3 Capability-Prediction Fitting Design Result Audit

## Metadata

- status: completed
- decision: `accept_m2896_capability_prediction_fitting_design_claim_safe_route_to_m2898_implementation_preflight`
- manifest: `experiments/manifests/m2897-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design-result-audit.json`
- audited design: `docs/m2896-paper-route-l0-l1-l2-l3-capability-prediction-fitting-design.md`
- parent synthesis: `docs/m2895-paper-route-l0-l1-l2-l3-capability-prediction-implementation-branch-synthesis.md`
- parent implementation audit: `docs/m2894-paper-route-l0-l1-l2-l3-capability-prediction-implementation-result-audit.md`
- parent implementation summary: `runs/m2893_paper_route_l0_l1_l2_l3_capability_prediction_implementation_preflight/summary.json`
- follow-up manifest: `experiments/manifests/m2898-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-preflight.json`
- next: `m2898-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-preflight`

## Audit Decision

M2897 accepts M2896 as a complete and claim-safe fitting design for one
bounded implementation preflight.

Formal decision:

```text
accept_m2896_capability_prediction_fitting_design_claim_safe_route_to_m2898_implementation_preflight
```

The accepted next action is M2898 implementation preflight. M2898 may implement
the fixed fitting recipe and may run bounded optimizer steps only as preflight
instrumentation. It may write fitted preflight weights, diagnostics, masks,
normalization rows, optimizer-step rows, baseline rows, rollback rows, claim
rows, and a follow-up result-audit manifest. It must not rank profiles, select
a winner, promote weights, claim model quality, claim paper evidence, claim
finite-window-vs-GRU evidence, claim current-sim or high-fidelity validation,
or claim level3 self-identification.

M2897 itself did not reset, step, roll out, replay, fit, train, run PPO, run an
optimizer step, persist fitted weights, validate, rank, select a winner,
promote a checkpoint, publish a package, or claim prediction quality, driver
performance, paper evidence, current-sim verdict, high-fidelity validation,
full-driver completion, finite-window-vs-GRU evidence, or level3
self-identification.

## Evidence Audited

M2896 was audited against the accepted M2890-M2895 chain:

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
actor observation dimension: 72
action dimension: 3
hidden/oracle actor input required: false
future target actor input required: false
evaluator targets actor visible: false
```

The audited M2893 implementation preflight reports `status_pass=true`,
`gate_matrix_pass=true`, all schema/loader/model-head smoke rows passing, no
optimizer step, no fitted weights, no fitting, no training, no validation, no
ranking, and no model-quality claim.

## Completeness Findings

M2896 defines a sufficiently complete objective contract for a bounded first
fitting preflight:

```text
continuous target loss: SmoothL1/Huber
binary recoverability loss: BCE-with-logits for explicitly binary available entries only
availability mask: required for every target scalar and profile row
loss-mass normalization: required
target-family weights: fixed to 1.0 for the first implementation preflight
non-finite target or prediction: hard failure
```

The target normalization and masking contract is sufficient:

```text
normalization source: train task_source_id split only
statistic: robust median and IQR or MAD per scalar
minimum finite entries for smoke: 2 per scalar
masked scalar semantics: unavailable target not zero target
paper holdout usage: forbidden
```

The split contract is sufficient and leakage-aware:

```text
split unit: task_source_id
forbidden split unit: profile_task_id
same task_source_id across profiles: assigned to one split
paper holdout admitted: false
ordinary validation denominator: false
ranking allowed: false
winner selection allowed: false
```

The optimizer scope is bounded enough for an implementation preflight:

```text
optimizer: AdamW
learning rate: 0.0003
weight decay: 0.0001
global-norm clipping: 1.0
max optimizer steps per profile: 128
seed list: 289800, 289801, 289802
early stopping: disabled
profile-specific tuning: forbidden
target-family weight tuning: forbidden
checkpoint promotion: forbidden
```

The baseline and diagnostic requirements are sufficient for implementation
failure detection:

```text
train-split target median baseline
train-split zero-normalized baseline
current-tiled L2 controls
L3 reset/truncation control
parameter-count rows
inference-cost proxy rows
profile metric diagnostics without ranking
```

The public-row overfit and rollback gates are sufficient for the next preflight:

```text
source-singleton rows excluded from proof and denominators
guard rows excluded from ordinary success denominators
smoke_eval task_source_id leakage fails closed
public-row-only improvement cannot become paper evidence
fresh/source-diverse panel remains required before paper claims
actor input and action contract changes roll back
hidden/oracle or future target actor visibility rolls back
unavailable target-as-zero usage rolls back
profile-specific optimizer budget or tuning rolls back
ranking or model-quality interpretation rolls back
```

## Claim Boundary

Accepted interpretation:

```text
M2896 is a claim-safe fitting design for one bounded M2898 implementation preflight.
```

Rejected interpretations:

```text
optimizer result
fitted model quality
training result
validation result
profile ranking
winner selection
checkpoint promotion
finite-window-vs-GRU verdict
current-response sufficiency
recurrent self-ID
paper evidence
current-sim verdict
high-fidelity validation readiness or result
full ideal driver completion
```

M2897 keeps the current public 17-row surface as implementation-preflight
material only. Any later paper or model-quality route still requires a
separate accepted result audit and a fresh/source-diverse or explicitly
synthesized generalization route.

## Follow-Up Route

M2897 registers and admits exactly one next route:

```text
m2898-paper-route-l0-l1-l2-l3-capability-prediction-fitting-implementation-preflight
```

M2898 must implement the accepted M2896 recipe over the accepted M2893 schema,
loader, target-mask, and model-head smoke surface. It must write:

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

M2898 must report all false-claim flags explicitly, including
`training_run`, `validation_run`, `ranking_run`, `model_quality_claim_made`,
`paper_claim_made`, `finite_window_vs_gru_claim_made`, and
`level3_self_id_claim_made`. Any bounded optimizer step and any persisted
preflight weights must remain implementation-preflight artifacts only.
