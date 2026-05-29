# M1641 Paper-Route Contour-Aware Exact Objective Projection Repair Result Audit

## Summary

M1641 audits the negative M1640 projection result before any tuned rerun.

Decision:

```text
contour_aware_projection_repair_audit_admit_damped_backtracking_design
```

M1640 is a clean negative result for the pre-registered Adam `lr=1e-3`
actor_mean-only projection recipe. The module and guardrails worked, gradients
reached `actor_mean`, and no checkpoint was written, but the optimizer step was
too large for the small `scale_1e-3` perturbation.

This audit does not run projection again, does not train, does not run PPO,
does not promote, does not use private holdout, does not change actor inputs,
does not treat diagnostics or donor-plus actions as loss targets, and does not
claim paper-level or level3 self-identification evidence.

## Audited Artifacts

```text
runs/m1640_contour_aware_exact_objective_projection_repair/summary.json
runs/m1640_contour_aware_exact_objective_projection_repair/repair_summary.csv
runs/m1640_contour_aware_exact_objective_projection_repair/guardrail_summary.csv
runs/m1640_contour_aware_exact_objective_projection_repair/optimization_trace.csv
docs/m1640-paper-route-contour-aware-exact-objective-projection-repair-implementation.md
```

## Result Classification

M1640 public smoke gate failed:

```text
passes_public_smoke_gates: false
null_result_classification: projection_residual_not_reduced
```

Failure taxonomy:

```text
training_instability
```

The label is used for projection optimizer instability. No environment
training or PPO ran.

## Residual Evidence

The initial perturbation was measurable:

```text
initial_positive_exact_residual_mean: 0.0003143580979667604
initial_positive_action_l2_max:       0.015652701258659363
initial_actor_mean_l2_to_base:        0.019672319293022156
```

The selected repaired candidate was unchanged from the initial perturbation:

```text
repaired_positive_exact_residual_mean: 0.0003143580979667604
repaired_positive_action_l2_max:       0.015652701258659363
repaired_actor_mean_l2_to_base:        0.019672319293022156
positive_exact_residual_reduction:     0.0
positive_exact_residual_reduction_ratio: 0.0
```

The trace shows a connected but unstable optimizer step:

```text
grad_norm_max: 4.537821292877197

step 0 residual: 0.0003143580979667604
step 1 residual: 0.03115139901638031
step 1 actor_mean_l2_to_base: 0.026685267686843872

best post-step residual: 0.0005202809115871787 at step 23
best post-step actor_mean_l2_to_base: 0.022058136761188507
```

No post-step candidate beat the initial residual, and every useful-looking
post-step candidate also expanded the actor_mean distance to base. Therefore
the M1640 best-trust-region candidate remained step 0.

## Guardrail Audit

M1640 guardrails stayed clean:

```text
repaired_checkpoint_written: false
checkpoint_weights_mutated: false
non_actor_mean_parameter_delta_max: 0.0
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

This separates the negative result from implementation or contract leakage.

## Supported Claims

M1641 supports:

```text
M1640 implemented the projection plumbing correctly enough to produce gradients and artifacts;
the exact objective still detects the controlled M1636 actor_mean perturbation;
the no-checkpoint and role guardrails are effective;
Adam lr=1e-3 is too aggressive for this scale_1e-3 actor_mean projection under the pre-registered trust metric;
a damped or backtracking projection design is justified before any rerun.
```

## Unsupported Claims

M1641 rejects or keeps unsupported:

```text
M1640 projection recipe passes;
projection repair is solved;
checkpoint artifact generation is admitted;
PPO proposal repair is admitted;
closed-loop driver performance improved;
private-holdout or promotion evidence exists;
paper-level evidence exists;
level3 anticipatory self-identification is proven.
```

## Why Not Tune Inside M1640

Changing M1640 after observing the failure would blur the pre-registered
evidence chain. The correct route is:

```text
record the negative result;
classify the optimizer-step blocker;
design the next projection recipe with its selection rule before rerun.
```

This preserves workflow discipline and prevents the exact-objective branch from
turning into untracked local parameter search on public rows.

## Next Route

Admit one design-only follow-up:

```text
m1642-paper-route-contour-aware-damped-projection-repair-design
```

M1642 should design, but not run, a damped full-batch exact-objective
projection repair. The design should pre-register:

```text
gradient scope: actor_mean.weight and actor_mean.bias only
loss: same M1632/M1638 positive exact residual
diagnostics: zero-weight evaluation only
candidate update: damped gradient or backtracking line search
acceptance: exact positive residual reduction plus actor_mean trust-region non-expansion
output: metrics only, no .pt checkpoint
blocked: PPO, closed-loop training/evaluation, promotion, private holdout, actor-input changes
```

The implementation should not be run until M1642 has fixed the step-size rule
and public-row overfit guardrails in writing.
