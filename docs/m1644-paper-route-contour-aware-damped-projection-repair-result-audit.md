# M1644 Paper-Route Contour-Aware Damped Projection Repair Result Audit

## Summary

M1644 audits the M1643 damped/backtracking projection pass before any checkpoint
artifact, PPO-proposal repair, or closed-loop route.

Decision:

```text
contour_aware_damped_projection_audit_admit_stress_test_design
```

M1643 is a clean positive objective-sanity result: the damped projection
reduced exact residual, preserved the actor_mean trust region, wrote no
checkpoint, avoided base interpolation, and kept all role guardrails clean.

The result is still local and public-row-specific. It is not yet enough to
write a repaired checkpoint, repair a PPO proposal, or claim closed-loop driver
progress. The next safe step is a design-only perturbation stress test over
multiple scales/seeds before any checkpoint artifact route.

## Audited Artifacts

```text
runs/m1643_contour_aware_damped_projection_repair/summary.json
runs/m1643_contour_aware_damped_projection_repair/projection_step_trace.csv
runs/m1643_contour_aware_damped_projection_repair/backtracking_candidate_trace.csv
runs/m1643_contour_aware_damped_projection_repair/repair_summary.csv
runs/m1643_contour_aware_damped_projection_repair/guardrail_summary.csv
docs/m1643-paper-route-contour-aware-damped-projection-repair-implementation.md
```

## Result Audit

M1643 passed:

```text
passes_public_smoke_gates: true
null_result_classification: contour_aware_exact_objective_projection_repair_public_pass
```

Exact residual reduction:

```text
initial_positive_exact_residual_mean:  0.0003143580979667604
repaired_positive_exact_residual_mean: 0.00003198102058377117
positive_exact_residual_reduction:     0.00028237707738298923
positive_exact_residual_reduction_ratio: 0.8982656378486144
```

Action residual reduction:

```text
initial_positive_action_l2_max:  0.015652701258659363
repaired_positive_action_l2_max: 0.005414916668087244
```

Trust-region metric:

```text
initial_actor_mean_l2_to_base:  0.019672319293022156
repaired_actor_mean_l2_to_base: 0.019625606015324593
actor_mean_l2_reduction:       0.00004671327769756317
```

Backtracking behavior:

```text
accepted_backtracking_step_count: 1
backtracking_candidate_count: 3
accepted_factor: 0.25
accepted_step_l2: 0.0012295199558138847
projection_stop_reason: target_reduction_reached
```

The pre-registered factors behaved as intended:

```text
factor 1.0 failed: residual_not_reduced
factor 0.5 failed: residual_not_reduced
factor 0.25 passed: residual reduced and trust preserved
```

## Guardrail Audit

M1643 guardrails were clean:

```text
repaired_checkpoint_written: false
checkpoint_weights_mutated: false
non_actor_mean_parameter_delta_max: 0.0
base_interpolation_used_for_repair: false
diagnostic_rows_used_as_positive: false
diagnostic_positive_weight_sum: 0
donor_plus_action_used_as_loss_target: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
labels_enter_actor_input: false
level3_self_id_claim_made: false
guardrail_violation_count: 0
```

Diagnostics improved, but remained zero-weight:

```text
initial_diagnostic_exact_residual_mean:  0.0002680706384126097
repaired_diagnostic_exact_residual_mean: 0.000035363835195312276
```

This is useful as a consistency signal, not as a training claim.

## Supported Claims

M1644 supports:

```text
M1643 fixed the M1640 optimizer-step instability for the controlled scale_1e-3 perturbation;
damped/backtracking exact projection can reduce local actor_mean policy-output residual;
the implementation enforces no-checkpoint, no-base-reset, diagnostics-zero-weight, and actor_mean-only guardrails;
the projection module is ready for a no-checkpoint perturbation stress-test design.
```

## Unsupported Claims

M1644 keeps unsupported:

```text
checkpoint artifact generation;
PPO-proposal repair;
closed-loop replay improvement;
behavior retention;
promotion;
private-holdout evidence;
paper-level evidence;
level3 anticipatory self-identification.
```

## Public-Row Overfit Risk

The M1643 pass is over one controlled perturbation:

```text
perturb_scale: 0.001
perturb_seed: 1639
positive rows: 39
diagnostic rows: 232
```

Because the target actions were generated from the base policy, this remains a
local objective-restoration probe. A checkpoint artifact would mostly encode
public-row exact-objective repair and could be mistaken for driver progress.

Before any checkpoint artifact or PPO-proposal repair, the projection rule
should be stress-tested without writing `.pt` files:

```text
multiple perturbation scales;
multiple perturbation seeds;
same positive/diagnostic roles;
same actor_mean-only scope;
same no-base-reset rule;
aggregate pass/fail summary;
mandatory audit afterward.
```

## Next Route

Admit design-only stress test:

```text
m1645-paper-route-contour-aware-damped-projection-stress-test-design
```

M1645 should design a no-checkpoint stress test over a small pre-registered
grid, such as:

```text
scales: [1e-4, 3e-4, 1e-3]
seeds:  [1645, 1646, 1647]
projection mode: damped_backtracking
outputs: per-candidate summary, aggregate summary, guardrail summary
pass rule: most candidates reduce residual; no guardrail violation; no checkpoint artifacts
```

M1644 does not admit checkpoint artifacts, PPO, promotion, private holdout,
actor-input changes, or level3 self-ID claims.
