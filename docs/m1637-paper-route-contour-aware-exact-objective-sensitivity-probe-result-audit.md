# M1637 Paper-Route Contour-Aware Exact Objective Sensitivity Probe Result Audit

## Summary

M1637 audits the M1636 exact-objective sensitivity probe.

Decision:

```text
contour_aware_sensitivity_audit_admit_projection_repair_design
```

This is a process audit only. It does not run actor update, train, run PPO,
promote a checkpoint, use private holdout, change actor inputs, treat
diagnostics as positive targets, treat `donor_plus_hidden_action` as a loss
target, or claim level3 self-identification.

## Audited Inputs

```text
runs/m1636_contour_aware_exact_objective_sensitivity_probe/summary.json
runs/m1636_contour_aware_exact_objective_sensitivity_probe/candidate_summary.csv
docs/m1636-paper-route-contour-aware-exact-objective-sensitivity-probe-implementation.md
```

## Audit Checks

M1636 passed the sensitivity gates:

```text
base_positive_exact_residual_mean: 0.0
base_positive_policy_action_residual_l2_max: 0.0
base_residual_near_zero: true
max_positive_exact_residual_mean_over_perturbations: 0.0003143580689195087
max_positive_policy_action_residual_l2_max_over_perturbations: 0.015652681982969475
measurable_perturbation_residual: true
perturbed_checkpoint_written: false
checkpoint_weights_mutated: false
actor_update_run: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
passes_public_smoke_gates: true
```

Candidate response was monotone enough for a smoke probe:

```text
scale 0.0   -> positive exact residual mean 0.0
scale 1e-4  -> positive exact residual mean 2.912e-06
scale 3e-4  -> positive exact residual mean 9.521e-05
scale 1e-3  -> positive exact residual mean 3.143e-04
```

Perturbed candidates correctly failed the M1633 zero-residual exact evaluator
gate. That is expected and is the signal used by M1636.

## Supported Claims

M1637 supports these narrow claims:

```text
the exact objective detects controlled actor_mean policy-output drift;
base remains zero-residual;
the sensitivity harness does not write perturbed checkpoints;
repair/projection design is now meaningful.
```

## Unsupported Claims

M1637 does not support:

```text
repair/projection works;
actor update is safe;
PPO proposal can be repaired;
closed-loop behavior improved;
checkpoint promotion is admitted;
private-holdout evidence is available;
paper-level validation is available;
level3 anticipatory self-identification is proven.
```

## Route Decision

Admit one design-only repair/projection milestone:

```text
m1638-paper-route-contour-aware-exact-objective-projection-repair-design
```

The next milestone should design how to reduce exact residual from a controlled
perturbed candidate back toward the base target without claiming closed-loop
improvement. Because the branch is approaching synthesis cadence, M1638 should
route to audit or branch synthesis before any repair implementation.

PPO, promotion, private holdout, and paper-level claims remain blocked.
