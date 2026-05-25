# M816 V4 Adaptive Primary Residual Calibration Design

## Purpose

M816 designs the first calibration route allowed by the M814 adaptive primary
corpus pass.

The design question is:

```text
How can the M814 source/axis-diverse primary low-margin corpus be used without
overfitting the public bracket rows or washing out existing residual behavior?
```

M816 is design-only:

```text
no implementation
no calibrator training
no actor update
no residual-head update
no PPO
no checkpoint promotion
```

## Starting Evidence

M814 produced a valid corpus:

```text
accepted_primary_raw_rows: 101
accepted_primary_rows: 85
unique_accepted_seeds: 9
unique_accepted_source_groups: 55
unique_accepted_fault_family_pairs: 8
unique_accepted_warmup_modes: 4
unique_accepted_boundary_axes: 3
result_class: v4_adaptive_boundary_bracketing_pass
```

Intervention diagnostics:

```text
reset_hidden_each_step collisions: 69 / 101
reset_hidden_then_normal collisions: 69 / 101
zero_command_obs collisions: 67 / 101
```

M815 audited this as a valid data-route pass, not a driver promotion.

## Calibration Boundary

M817 may train a separate calibrator only.

Frozen:

```text
M568 actor backbone
M568 recurrent policy parameters
M761 residual head
actor observation contract
alpha base value = 0.2
primary margin threshold = 0.00005
```

Trainable:

```text
a small residual gate / calibrator module only
```

The deploy-time actor input must not change. The calibrator may consume only
features already available to the residual pathway or deterministic residual
features generated from the frozen actor/residual computation. It must not use
labels such as success, collision, margin, or fault identity at inference time.

## Proposed Calibrator

M817 should start conservative:

```text
calibrated_residual = gate_phi(features) * residual
action = base_action + alpha * calibrated_residual
```

Two variants may be implemented, but evaluated separately:

```text
scalar_gate:
  one gate shared by steer/throttle/brake residuals

vector_gate:
  three gates, one per action dimension
```

Gate constraints:

```text
gate in [0.0, 1.0]
initial gate near 1.0
identity regularization strong by default
no gate may add residual beyond M761 output
```

This prevents the calibrator from becoming a new high-authority policy.

## Source-Heldout Split

M817 must create a deterministic split before training:

```text
split unit:
  source_group_id + seed + fault_family_pair

train:
  about 70 percent of split units

holdout:
  about 30 percent of split units
  disjoint source_group_id values
  preserve at least 2 boundary axes if possible
  preserve at least 3 fault-family pairs if possible
```

The split artifact must be written before optimization:

```text
runs/m817_v4_adaptive_primary_residual_calibration/split_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/split_summary.json
```

If a valid holdout cannot be formed, M817 must stop before training and
classify the result as `split_invalid`.

## Objective

The objective should be lexicographic in spirit:

```text
1. do not break normal primary rows
2. preserve intervention sensitivity
3. preserve old residual behavior
4. keep the calibrator close to identity
```

Recommended losses:

```text
L_normal_margin:
  penalize train normal rows that become collision or negative-margin under
  calibrated replay

L_primary_window:
  discourage pushing primary rows far outside the low-margin band, but with
  lower priority than avoiding collision

L_intervention_sensitivity:
  preserve margin drop or collision under reset/zero-command interventions
  for rows where M814 showed intervention sensitivity

L_identity:
  keep gate close to 1.0 unless needed by the other losses

L_smooth_gate:
  discourage large gate changes between neighboring rows from the same source
```

M817 should not train directly on holdout rows.

## Exact Gates

After any candidate calibrator is trained, M817 must run exact closed-loop
evaluation in this order:

```text
1. M814 train split exact normal primary retention
2. M814 holdout split exact normal primary retention
3. M814 train split intervention sensitivity retention
4. M814 holdout split intervention sensitivity retention
5. old public residual replay / behavior retention gates from the M761-M814 branch
6. checksum and no-PPO invariants
```

Minimum acceptance for a calibration candidate:

```text
holdout normal collision count == 0
holdout normal success count == holdout row count
holdout accepted primary rows remain finite and non-collision
holdout intervention collision/drop rate does not collapse by more than 10 percent absolute
old replay / behavior gates do not regress relative to M761 alpha 0.2 baseline
actor checksum unchanged
M761 residual-head checksum unchanged
optimizer touches only calibrator parameters
ppo_used == false
promoted == false
```

If train improves but holdout regresses, classify as `objective_overfit`.

## Outputs

M817 should write:

```text
src/autodrift/v4_adaptive_primary_residual_calibration.py
tests/test_v4_adaptive_primary_residual_calibration.py
runs/m817_v4_adaptive_primary_residual_calibration/summary.json
runs/m817_v4_adaptive_primary_residual_calibration/split_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/split_summary.json
runs/m817_v4_adaptive_primary_residual_calibration/train_eval_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/holdout_eval_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/intervention_eval_rows.csv
runs/m817_v4_adaptive_primary_residual_calibration/gate_summary.csv
docs/m817-v4-adaptive-primary-residual-calibration-implementation.md
```

If a calibrator checkpoint is produced, it is an experiment artifact only:

```text
runs/m817_v4_adaptive_primary_residual_calibration/calibrator.pt
```

It is not a promoted driver checkpoint.

## Result Classes

M817 should classify:

```text
v4_adaptive_primary_residual_calibration_candidate
v4_adaptive_primary_residual_calibration_split_invalid
v4_adaptive_primary_residual_calibration_holdout_regression
v4_adaptive_primary_residual_calibration_intervention_washout
v4_adaptive_primary_residual_calibration_old_gate_regression
v4_adaptive_primary_residual_calibration_objective_overfit
v4_adaptive_primary_residual_calibration_contract_violation
```

Only `candidate` may route to an audit. It still must not promote a driver.

## Decision

Decision:

```text
adaptive_primary_residual_calibration_design_admit_m817
```

Next blocker:

```text
m817-v4-adaptive-primary-residual-calibration-implementation
```

M817 may implement the calibration probe. It must not update actor weights, run
PPO, or promote a checkpoint.
