# M1359 Paper-Route Bidirectional Active-Set Probe Design

## Summary

M1359 designs the first no-PPO probe that should consume the combined
correct-history and wrong-history trajectory anchor exported by M1358.

Decision:

```text
bidirectional_active_set_probe_design_admit_implementation
```

The next implementation should not be a PPO run and should not promote a
checkpoint. It should test one narrow question:

```text
Can a no-PPO source-history update improve exact materialized metrics while
preserving both correct-history replay safety and wrong-history replay failure
behavior?
```

## Inputs

Base checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Source-history objective corpus:

```text
runs/m1336_materialized_source_history_objective_corpus_export
```

Combined bidirectional active-set anchor:

```text
runs/m1358_bidirectional_active_set_anchor_export/combined_recovery_rejected_anchor.npz
```

Replay preflight order:

```text
1. M267/M264 current-family boundary replay
2. M183/M170 old-family boundary replay only if M267/M264 passes
```

## Objective

The implementation should reuse the M1355 update structure but replace the
freshly exported normal-only retention anchor with the M1358 combined anchor.

Proposed loss:

```text
L = L_source_pair_group
  + lambda_anchor * L_bidirectional_trajectory_anchor
  + lambda_trust * L_parameter_trust_region
```

Where:

```text
L_source_pair_group:
  M1336/M1342 materialized source-history pair-group objective.

L_bidirectional_trajectory_anchor:
  exact trajectory action anchor over the M1358 combined NPZ.
  The NPZ already carries per-row weights. The implementation should respect
  those weights rather than rebuilding row pressure inside the update loop.

L_parameter_trust_region:
  same role as M1355, keeping the update bounded around M1154.
```

This objective is intentionally asymmetric through the anchor data:

```text
correct-history rows:
  retain safe normal trajectories.

wrong-history rows:
  retain rejected/wrong-history trajectories for rows 6, 10, 13, 15, 16.
```

The wrong-history branch is not deployed behavior. It is an intervention surface
used to prove that the actor's action depends on history state.

## Trainable Scope

Keep the M1355 trainable scope:

```text
response_context_fusion.0.*
actor_mean.*
```

Required mutation checks:

```text
forbidden_parameter_mutation_detected=false
log_std_l2=0.0
actor_input_contract_changed=false
```

Do not add actor inputs. Do not change the canonical 72-value human-view frame.

## Evaluation Order

The probe should stop early by pre-registered order:

```text
1. checkpoint contract and mutation-scope checks
2. exact source-history metrics vs M1154
3. M267/M264 replay gate
4. M183/M170 replay gate only if M267/M264 passes
5. result audit before any wider replay, PPO, or promotion
```

M267/M264 must retain:

```text
normal_success_delta >= 0.0
success_drop_count_delta >= 0
wrong-history safe rows must not include 6, 10, 13, 15, or 16
```

Exact metrics should be compared against:

```text
M1154 public base
M1352 alpha 0.005 diagnostic
M1355 normal-retention negative result
```

## Failure Taxonomy

Use these result classes:

```text
no_exact_lift:
  exact source-history metrics do not improve.

normal_branch_proof_washout:
  M267/M264 or M183/M170 normal-history success/margin collapses.

wrong_branch_proof_washout:
  M267/M264 wrong-history rows 6, 10, 13, 15, or 16 become safe again.

contract_artifact:
  mutation scope, log_std, actor-input contract, or forbidden shortcut check
  fails.

probe_pass:
  exact metrics improve and both replay preflight surfaces pass.
```

Even `probe_pass` is not a promotion result. It should route to a result audit.

## Guardrails

M1359 performs no training, PPO, actor update, replay run, private holdout,
promotion, threshold relaxation, actor-input expansion, high-fidelity claim,
paper-level claim, or closed-loop self-identification claim.

## Next

```text
m1360-paper-route-bidirectional-active-set-probe-implementation
```

M1360 should implement and run exactly one no-PPO bidirectional active-set probe
using the M1358 combined anchor. If it fails, classify the failure before tuning
coefficients.
