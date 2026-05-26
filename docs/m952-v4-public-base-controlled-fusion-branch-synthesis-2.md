# M952 V4 Public Base Controlled Fusion Branch Synthesis 2

## Purpose

M952 synthesizes the controlled-fusion branch after M951. It is a process gate,
not a training or replay milestone.

M952 does not train, run replay, run PPO, change actor inputs, or promote.

## Evidence Summary

The branch started from the controlled-fusion surface:

```text
allowed:
  actor_mean.*
  response_context_fusion.0.*

forbidden:
  response_encoder.*
  context_encoder.*
  online_gru_cell.*
  critic.*
  log_std
  actor inputs
```

M942 found exact-objective candidates on the M940 raw direction:

```text
strict_candidate_count: 3
candidate alphas: 0.0675, 0.0700, 0.0725
training/replay/PPO/promotion: blocked
```

M944 materialized those candidates and confirmed exact compatibility from
ordinary checkpoint loading:

```text
materialized_checkpoint_count: 3
exact_candidate_count: 3
primary_candidate_exact_pass: true
forbidden_parameter_changed: false
```

M946 ran the closed-loop replay/proof gate. It rejected the primary candidate:

```text
public replay gates passed: 5 / 6
failed surface: M267/M264
M267/M264 success_drop_count: 17 -> 13
behavior seeds 9505/9506: pass
result: proof_washout
```

M947 showed the failure was not alpha `0.0725` overshoot:

```text
alpha 0.0675: M267/M264 success_drop_count 17 -> 13
alpha 0.0700: M267/M264 success_drop_count 17 -> 13
alpha 0.0725: M267/M264 success_drop_count 17 -> 13
failed rows: 6, 13, 15, 16
```

M949 added rejected-branch retention proxies. This made M267 preflight live but
still produced no exact candidate:

```text
m267_preflight_pass_alphas: 0.005, 0.010, 0.200
exact_candidate_alpha_count: 0
candidate_alpha_count: 0
```

M951 ran the one bounded lower-boundary retune admitted by M950:

```text
m267_preflight_pass_alpha_count: 13
exact_candidate_alpha_count: 0
candidate_alpha_count: 0
result: objective_conflict
```

After M951, the rejected-history proof side is mostly solved, but the original
normal-retention versus low-tail-lift conflict remains:

```text
alphas <= 0.050:
  normal_retention_pass: true
  tail_lift_pass: false
  M267 preflight: pass

alphas >= 0.0675:
  normal_retention_pass: false
  tail_lift_pass: true
  M267 preflight: pass through 0.150
```

## Supported Claims

- The controlled-fusion trainable surface is implemented correctly. Across
  M937-M951, forbidden parameters and actor inputs stayed unchanged when
  required.
- The surface has real low-tail leverage. M942/M944 found exact-objective
  candidates, and M951 shows tail-lift is achievable.
- Exact objective compatibility is not enough. M946 proved an exact-compatible
  candidate can wash out wrong-history proof rows.
- The M267/M264 replay preflight is live and useful. It caught the M944 failure
  and confirmed M949/M951 rejected-branch retention effects.
- Rejected-branch retention proxies can protect the M267 proof rows. M951
  improved M267 preflight from zero candidate overlap to `13` pass alphas.

## Falsified Claims

- Falsified: the M944 exact-compatible controlled-fusion candidates are replay
  admissible.
- Falsified: lowering to the known backup alphas `0.0675` or `0.0700` is enough.
- Falsified: adding one-step rejected-branch action retention to the same local
  objective is enough to create exact/preflight overlap.
- Falsified: one more lower-boundary coefficient retune is enough.
- Falsified: more local coefficient tweaking on the same objective is justified
  without synthesis.

## Failure Taxonomy Summary

```text
M946: proof_washout
M947: proof_washout diagnosis
M949: objective_overfit / objective_conflict
M951: objective_overfit / controlled-fusion trust-region conflict
```

This is no longer a single protected-key issue and no longer a pure
wrong-history retention issue. The branch is now blocked by a controlled-fusion
trust-region conflict under the registered exact thresholds.

## Public-Gate Overfit Risk

Risk is high. The branch has repeatedly optimized around the same public
objective rows and M267/M264 proof surface. Continuing local retunes would make
the harness increasingly good at fitting these public rows without proving a
general mechanism.

This is exactly the workflow-synthesis stop condition: do not create another
narrow local objective milestone after the one bounded retune fails.

## Next Branch Decision

Synthesis decision:

```text
pivot
```

Do not continue the current local controlled-fusion coefficient-tuning branch.
Do not open encoders or GRU yet.
Do not run PPO.
Do not promote.

The next branch should answer a more basic feasibility question before more
training:

```text
Can we mine or construct replay-constrained targets that simultaneously:
1. preserve normal-retention thresholds,
2. improve low-tail objective metrics,
3. preserve M267/M264 wrong-history failure rows?
```

If such targets do not exist inside the current action/trust region, widening
the actor surface or adding objectives is premature.

Next blocker:

```text
m953-v4-public-base-replay-constrained-target-feasibility-design
```
