# M1360 Paper-Route Bidirectional Active-Set Probe Implementation

## Summary

M1360 implemented and ran the first no-PPO bidirectional active-set probe using
the M1358 combined anchor.

Decision:

```text
bidirectional_active_set_probe_m267_margin_gap_washout_route_to_result_audit
```

This is a negative public proof result, but it is more informative than M1355.
The update strongly improves exact source-history metrics and preserves both
M267/M264 normal success and wrong-history success-drop count. It still fails
M267/M264 because the mean margin gap regresses just beyond the pre-registered
threshold.

## Implementation

New module:

```text
src/autodrift/materialized_source_history_bidirectional_active_set_probe.py
```

New tests:

```text
tests/test_materialized_source_history_bidirectional_active_set_probe.py
```

The probe uses:

```text
base checkpoint:
  runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt

source-history corpus:
  runs/m1336_materialized_source_history_objective_corpus_export

bidirectional anchor:
  runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
```

The trainable scope remains:

```text
response_context_fusion.0.*
actor_mean.*
```

No actor input changed.

## Numerical Fix

The first M1360 attempt exposed a reusable numerical issue: the combined anchor
contains rows whose reference action exactly matches the current actor action.
The radius-hinge trajectory loss previously used:

```text
sqrt(clamp(action_mse, min=0.0))
```

At exact zero error this can produce non-finite gradients. M1360 fixes the shared
loss with a tiny lower bound:

```text
sqrt(clamp(action_mse, min=1.0e-12))
```

A regression test now verifies finite gradients for exact-zero trajectory anchor
rows.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.materialized_source_history_bidirectional_active_set_probe \
  --run-dir runs/m1360_bidirectional_active_set_probe \
  --device cpu
```

## Result

Result class:

```text
materialized_source_history_bidirectional_active_set_m267_proof_washout
```

Failure taxonomy:

```text
proof_washout
```

Key exact metrics:

```text
combined_loss_delta: -4.7206263688
full_group_min_joint_margin_delta: +5.3494348235
eval_fold_group_min_joint_margin_delta: +4.9267139186
beat_alpha005_exact_lift: true
beat_m1355_exact_lift: true
```

Mutation checks:

```text
forbidden_parameter_mutation_detected: false
log_std_l2: 0.0
changed_parameter_names:
  actor_mean.bias
  actor_mean.weight
  response_context_fusion.0.bias
  response_context_fusion.0.weight
```

M267/M264 replay:

```text
gate_pass: false
normal_success_delta: 0.0
normal_margin_mean_delta: -0.0028695719
success_drop_count_delta: 0
wrong_history_success_delta: 0.0
margin_gap_mean_delta: -0.0012517729
max_margin_gap_regression: 0.001
wrong_safe_required_row_ids: []
```

M183/M170 was not run because M267/M264 failed by the pre-registered order.

## Interpretation

M1360 fixes the M1355 wrong-branch failure:

```text
M1355: success_drop_count_delta = -5
M1360: success_drop_count_delta = 0
```

It also keeps normal history successful:

```text
M1360 normal_success_delta = 0.0
```

The remaining failure is narrower:

```text
wrong-history remains failing, but the normal-vs-wrong margin gap shrinks by
0.0012517729, slightly beyond the allowed 0.001 threshold.
```

So the branch-asymmetric anchor is doing the intended high-level job. It is not
yet replay-safe because the gap margin is still too tight.

## Guardrails

M1360 runs one no-PPO actor update. It performs no PPO, promotion, private
holdout, full replay, threshold relaxation, actor-input expansion, high-fidelity
claim, paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1361-paper-route-bidirectional-active-set-probe-result-audit
```

The audit should decide whether the next control variable is interpolation or a
gap-aware active-set term. Do not tune coefficients in-place before the audit.
