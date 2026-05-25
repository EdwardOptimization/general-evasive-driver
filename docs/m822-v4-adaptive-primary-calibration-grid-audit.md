# M822 V4 Adaptive Primary Calibration Grid Audit

## Purpose

M822 audits the M821 fixed scalar/vector calibration grid result before any
further calibration design.

The audit question is:

```text
Did M821 find a useful fixed residual gate, or does the branch need to stop
fixed-gate tuning on this corpus?
```

M822 is audit-only:

```text
no replay
no calibrator training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Evidence Inspected

Primary artifacts:

```text
runs/m821_v4_adaptive_primary_calibration_grid/summary.json
runs/m821_v4_adaptive_primary_calibration_grid/candidate_grid.csv
runs/m821_v4_adaptive_primary_calibration_grid/train_candidate_metrics.csv
runs/m821_v4_adaptive_primary_calibration_grid/holdout_candidate_metrics.csv
runs/m821_v4_adaptive_primary_calibration_grid/intervention_candidate_metrics.csv
runs/m821_v4_adaptive_primary_calibration_grid/gate_summary.csv
docs/m821-v4-adaptive-primary-calibration-grid-implementation.md
```

M821 result class:

```text
v4_adaptive_primary_calibration_identity_only
```

## Artifact Consistency

M821 produced the required artifacts:

```text
candidate_count: 53
normal_eval_row_count: 4505
intervention_eval_row_count: 13515
merged_rows: 85
train_rows: 57
holdout_rows: 28
source_group_disjoint: true
snapshot_lookup_rows: 110
identity_normal_rows: 85
```

Candidate selection was train-only:

```text
selection_used_holdout: false
selected_candidate_id: identity
selected train_rank: 1
```

## Contract Audit

Frozen parameters stayed frozen:

```text
actor_backbone_changed: false
residual_head_changed: false
trained_adaptive_calibrator: false
ppo_used: false
promoted: false
checkpoint_promoted: false
```

Checksums:

```text
base_actor_checksum_before: d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
base_actor_checksum_after:  d9f636b495426c606140d15ddc207243979e87f1effbd89deb2946ae7c874c88
residual_head_checksum_before: 87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
residual_head_checksum_after:  87f7bf7359ee0e23d5b388fa6759cc8056c6acf2a828797f70cb118ed44b4b94
```

The contract is clean. This is not a contract failure.

## Candidate Ranking Audit

Train-only ranking:

```text
rank 1: identity
rank 2: scalar 0.999
rank 3: scalar 0.980
rank 4: scalar 0.950
rank 5: vector steer=1.0 throttle=1.0 brake=0.75
```

Identity train metrics:

```text
normal_success_count: 57 / 57
normal_collision_count: 0
normal_margin_p05: 0.000004498630057403475
normal_margin_lift_p05: 0.0
normal_margin_lift_mean: 0.0
intervention collision rate: 0.6783625730994152
action_drift_mean: 0.0
```

Identity holdout metrics:

```text
normal_success_count: 28 / 28
normal_collision_count: 0
normal_margin_p05: 0.000007132857149438898
normal_margin_lift_p05: 0.0
normal_margin_lift_mean: 0.0
intervention collision rate: 0.7023809523809523
action_drift_mean: 0.0
```

Best non-identity candidates did not improve p05 margin lift:

```text
scalar 0.999:
  train p05 lift:   -0.0000001068632457190688
  holdout p05 lift: -0.0000006666190849768938

scalar 0.980:
  train p05 lift:   -0.0000021826446794381837
  holdout p05 lift: -0.000013461451240159847

scalar 0.950:
  train p05 lift:   -0.000005450293785180804
  holdout p05 lift: -0.000033604458567493276

vector 1.0 / 1.0 / 0.75:
  train p05 lift:   -0.000006573407625998229
  holdout p05 lift: -0.000009029492403678229
```

This is a clean fixed-gate negative: the closest non-identity candidates are
near identity and still reduce low-margin robustness.

## Gate Audit

M821 gate summary:

```text
actor_checksum_unchanged: pass
residual_head_checksum_unchanged: pass
train_selection_pass: pass
holdout_acceptance_pass: pass
selected_strong_candidate: fail
```

The holdout acceptance pass belongs to identity only. It must not be read as a
fixed-gate improvement.

The failing `selected_strong_candidate` gate is the decisive result:

```text
no non-identity fixed gate meets the margin-lift threshold.
```

## Supported Claims

M821 supports:

- the fixed-gate grid harness works and produces complete exact artifacts;
- train-only selection was respected;
- holdout was not used for candidate selection;
- identity is the best train-selected candidate;
- fixed scalar/vector residual suppression does not improve the strict
  low-margin primary corpus;
- intervention sensitivity and old behavior are retained by identity;
- actor and M761 residual-head contract boundaries remain intact.

## Falsified Or Unsupported Claims

M821 falsifies or fails to support:

```text
A fixed scalar residual gate can improve this source-heldout corpus.
```

```text
A fixed vector residual gate can improve this source-heldout corpus.
```

```text
Residual suppression is the right control variable for the current M814/M817
low-margin rows.
```

M821 does not support:

- learned adaptive gate training;
- PPO admission;
- checkpoint promotion;
- threshold relaxation;
- continuing to tune fixed gates on the same public corpus.

## Failure Taxonomy

### metric_artifact

This is the primary audit label. Identity passes all retention gates, but that
does not mean the grid produced useful new driver behavior.

### objective_overfit

Not observed as a train-positive / holdout-negative fixed-gate result. The
train side never selected a non-identity gate.

### behavior_regression

Not observed for identity. Some non-identity gates introduce action drift and
negative margin lift, but they are rejected before any candidate claim.

Rejected labels:

```text
contract_violation
training_instability
proof_washout
promotion_gate_failure
private_holdout_contamination
```

## Decision

Decision:

```text
stop_fixed_gate_calibration_on_m814_m817_corpus
```

M822 closes the fixed scalar/vector gate route on this corpus. Further progress
requires a new route, not more fixed-gate tuning against the same public rows.

The next step should be design-only and should decide between:

```text
1. a new data route with richer hidden dynamics / fault diversity;
2. a diagnostic objective that does not merely suppress residual authority;
3. stopping this calibration sub-branch and returning to broader self-ID tasks.
```

Blocked:

```text
fixed-gate calibration candidate
learned adaptive gate training from this result alone
PPO
checkpoint promotion
threshold relaxation
```

Next blocker:

```text
m823-v4-adaptive-primary-calibration-next-route-design
```
