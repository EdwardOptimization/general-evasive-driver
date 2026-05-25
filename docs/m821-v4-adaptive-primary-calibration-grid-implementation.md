# M821 V4 Adaptive Primary Calibration Grid Implementation

## Purpose

M821 implements and runs the exact fixed-gate calibration grid admitted by M820.

The experiment question is:

```text
Can any fixed scalar or fixed vector residual gate beat identity on the M814
source-heldout primary corpus while preserving intervention sensitivity and
old behavior?
```

M821 is infrastructure-only:

```text
no actor update
no M761 residual-head update
no learned adaptive calibrator training
no PPO
no checkpoint promotion
```

## Implementation

New source:

```text
src/autodrift/v4_adaptive_primary_calibration_grid.py
```

New tests:

```text
tests/test_v4_adaptive_primary_calibration_grid.py
```

The implementation adds:

- a parameter-free `FixedResidualGate`;
- deterministic merge of M814 accepted rows with the M817 source-heldout split;
- identity exact replay baseline;
- fixed scalar residual gates;
- fixed vector/action-dimension residual gates;
- train-only candidate ranking;
- holdout-only acceptance;
- exact intervention replay for every fixed gate;
- checksum guards for frozen actor and M761 residual head.

The evaluated action equation is:

```text
action = base_action + 0.2 * fixed_gate * residual_M761(features)
```

with:

```text
fixed_gate in scalar/vector grid
actor frozen
M761 residual head frozen
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.v4_adaptive_primary_calibration_grid \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --accepted-rows runs/m814_v4_adaptive_boundary_bracketing/accepted_primary_rows.csv \
  --split-rows runs/m817_v4_adaptive_primary_residual_calibration/split_rows.csv \
  --intervention-rows runs/m814_v4_adaptive_boundary_bracketing/intervention_replay_rows.csv \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --run-dir runs/m821_v4_adaptive_primary_calibration_grid \
  --device cpu
```

## Result

Run directory:

```text
runs/m821_v4_adaptive_primary_calibration_grid
```

Summary:

```text
result_class: v4_adaptive_primary_calibration_identity_only
candidate_count: 53
normal_eval_row_count: 4505
intervention_eval_row_count: 13515
merged_rows: 85
train_rows: 57
holdout_rows: 28
source_group_disjoint: true
snapshot_lookup_rows: 110
identity_normal_rows: 85
elapsed_seconds: 172.73711490631104
```

Selected candidate:

```text
selected_candidate_id: identity
family: identity
steer_gate: 1.0
throttle_gate: 1.0
brake_gate: 1.0
selection_used_holdout: false
```

The train-only ranking chose identity:

```text
rank 1: identity
rank 2: scalar 0.999
rank 3: scalar 0.980
rank 4: scalar 0.950
rank 5: vector steer=1.0 throttle=1.0 brake=0.75
```

No non-identity candidate produced positive train p05 margin lift.

## Train Metrics

Selected train metrics:

```text
normal_rows: 57
normal_success_count: 57
normal_collision_count: 0
normal_margin_min: 0.0000018321560406597825
normal_margin_mean: 0.00002742294610893403
normal_margin_p05: 0.000004498630057403475
normal_margin_lift_p05: 0.0
normal_margin_lift_mean: 0.0
action_drift_mean: 0.0
action_drift_max: 0.0
baseline_intervention_collision_rate: 0.6783625730994152
calibrated_intervention_collision_rate: 0.6783625730994152
selection_pass: true
train_rank: 1
```

Top non-identity train candidates were worse on p05 margin lift:

```text
scalar 0.999 p05 lift: -0.0000001068632457190688
scalar 0.980 p05 lift: -0.0000021826446794381837
scalar 0.950 p05 lift: -0.000005450293785180804
vector 1.0/1.0/0.75 p05 lift: -0.000006573407625998229
```

## Holdout Metrics

Selected holdout metrics:

```text
normal_rows: 28
normal_success_count: 28
normal_collision_count: 0
normal_margin_min: 0.0000019577745300480842
normal_margin_mean: 0.000027676263365083997
normal_margin_p05: 0.000007132857149438898
normal_margin_lift_p05: 0.0
normal_margin_lift_mean: 0.0
action_drift_mean: 0.0
action_drift_max: 0.0
baseline_intervention_collision_rate: 0.7023809523809523
calibrated_intervention_collision_rate: 0.7023809523809523
holdout_acceptance_pass: true
strong_candidate_pass: false
```

Top non-identity holdout candidates were also worse on p05 margin lift:

```text
scalar 0.999 p05 lift: -0.0000006666190849768938
scalar 0.980 p05 lift: -0.000013461451240159847
scalar 0.950 p05 lift: -0.000033604458567493276
vector 1.0/1.0/0.75 p05 lift: -0.000009029492403678229
```

## Contract Checks

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

Gate summary:

```text
actor_checksum_unchanged: pass
residual_head_checksum_unchanged: pass
train_selection_pass: pass
holdout_acceptance_pass: pass
selected_strong_candidate: fail
```

The `selected_strong_candidate` gate failing is expected for an identity-only
classification. It blocks any fixed-gate candidate claim.

## Interpretation

M821 is a clean negative for fixed scalar/vector residual suppression on this
M814/M817 source-heldout corpus.

It supports:

- the exact grid implementation works and writes all required artifacts;
- identity is the best train-selected candidate;
- fixed residual suppression does not improve p05 or mean normal-margin lift;
- intervention sensitivity is preserved by identity;
- actor and M761 residual-head contract boundaries remain intact.

It does not support:

- a fixed scalar gate candidate;
- a fixed vector gate candidate;
- a learned adaptive calibrator;
- PPO admission;
- checkpoint promotion.

The result strengthens M818's warning: retention gates alone are insufficient.
On this corpus, reducing M761 residual authority hurts low-margin robustness
more than it helps.

## Decision

Classification:

```text
v4_adaptive_primary_calibration_identity_only
```

Next blocker:

```text
m822-v4-adaptive-primary-calibration-grid-audit
```

M822 should audit this as an identity-only fixed-gate negative before deciding
whether to stop calibrator tuning on this corpus, pivot to new data, or design a
different objective.

## Verification

```text
python -m compileall -q src/autodrift/v4_adaptive_primary_calibration_grid.py tests/test_v4_adaptive_primary_calibration_grid.py
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_v4_adaptive_primary_calibration_grid.py
```

Result:

```text
5 passed
```
