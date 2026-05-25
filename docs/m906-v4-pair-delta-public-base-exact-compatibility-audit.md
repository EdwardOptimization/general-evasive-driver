# M906 V4 Pair-Delta Public-Base Exact Compatibility Audit

## Purpose

M906 attempted the exact no-update pair-delta objective compatibility audit for
the current public-gate base.

Checkpoint:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

Residual head:

```text
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

M906 did not train, run replay, run PPO, or promote.

## Result

M906 failed before tensor reconstruction:

```text
ValueError: residual feature_dim=64 does not match actor feature_dim=128
```

Failure summary:

```text
result_class: public_base_exact_compatibility_feature_dim_mismatch
failed_before_reconstruction: true
tensor_rows_reconstructed: 0
residual_feature_dim: 64
expected_actor_feature_dim: 128
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
actor_parameters_changed: false
```

Artifact:

```text
runs/m906_public_base_exact_compatibility/summary.json
```

## Interpretation

M906 confirms that the M568-rooted pair-delta objective tooling cannot be
directly applied to the current public-gate base with the M761 residual head.

This is not a driver failure and not a PPO failure. It is a compatibility and
lineage blocker:

```text
M761 residual head feature_dim: 64
M399 public-base actor feature_dim: 128
```

The public base and diagnostic base must remain separated until the feature
dimension/architecture mismatch is resolved.

## Supported Claims

M906 supports:

```text
The public-base integration branch correctly found a real compatibility blocker
before attempting an update.

The blocker occurs before replay, training, or promotion.

Direct public-base objective-only update with the M761 residual head is blocked.
```

## Unsupported Claims

M906 does not support:

```text
public-base objective update feasibility;
public-base replay retention;
PPO safety;
public-base promotion;
actor-input contract violation.
```

The mismatch is feature architecture compatibility, not evidence that the actor
uses forbidden inputs.

## Decision

Decision:

```text
public_base_exact_compatibility_blocked_feature_dim_mismatch
```

Next:

```text
m907-v4-pair-delta-public-base-feature-dim-compatibility-audit
```

M907 should audit the feature-dimension mismatch and decide whether the next
route is:

```text
train or derive a public-base-compatible residual head;
write an adapter/compatibility layer;
reconstruct objective tensors without M761 residual features;
or keep public-base integration blocked and return to M568 diagnostic branch.
```

M907 must not train or change model inputs.
