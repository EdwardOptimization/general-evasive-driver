# M907 V4 Pair-Delta Public-Base Feature-Dim Compatibility Audit

## Purpose

M907 audits the M906 blocker:

```text
ValueError: residual feature_dim=64 does not match actor feature_dim=128
```

This milestone is process/compatibility only:

```text
no training
no actor update
no replay
no PPO
no checkpoint promotion
no actor input change
```

## Read-Only Inspection

The public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

has:

```text
actor_encoder: human_view_online_gru
obs_dim: 72
actor_feature_dim: 128
act_dim: 3
response_dim: 12
context_dim: 60
online_recurrent: true
action_sequence_horizon: 1
```

The diagnostic BC base:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

has:

```text
actor_encoder: human_view_online_gru
obs_dim: 72
actor_feature_dim: 64
act_dim: 3
response_dim: 12
context_dim: 60
online_recurrent: true
action_sequence_horizon: 1
```

The M761 residual head:

```text
runs/m761_v4_sequence_objective_probe/residual_head.pt
```

has:

```text
feature_dim: 64
max_residual: 0.04
net.0.weight: 64 x 64
net.0.bias: 64
net.2.weight: 3 x 64
net.2.bias: 3
```

## Interpretation

The M906 failure is an architecture compatibility blocker.

It is not an actor-input contract violation:

```text
M399 obs_dim: 72
M568 obs_dim: 72
M399/M568 actor_encoder: human_view_online_gru
M399/M568 response_dim: 12
M399/M568 context_dim: 60
```

Both actors still satisfy the P0 human-view no-wheel actor contract. The
incompatible dimension is the internal recurrent actor feature width:

```text
M399 actor feature_dim: 128
M568 actor feature_dim: 64
M761 residual feature_dim: 64
```

The M761 residual head is therefore tied to the M568 feature representation. It
cannot be loaded against M399 without either retraining a 128-dim residual head
or introducing an unvalidated representation adapter.

## Route Options

Rejected route:

```text
force-load or pad the M761 residual head
```

Reason:

```text
The first linear layer is trained on a 64-dim M568 feature basis. Zero-padding,
projection, or truncation would create an unregistered representation mapping
with no proof that the residual semantics transfer to the M399 128-dim feature
space.
```

Rejected route:

```text
modify actor inputs to match the residual head
```

Reason:

```text
The mismatch is not an observation mismatch. Changing actor inputs would be a
contract risk and would not solve the internal feature-basis mismatch.
```

Deferred route:

```text
residual-free objective sanity
```

Reason:

```text
This can be useful as a diagnostic, but it does not produce a deployable or
testable public-base correction direction. The current branch needs a
public-base-compatible exact objective path.
```

Selected route:

```text
design a public-base-compatible residual-head objective probe
```

The next design should:

```text
use M399 as the frozen base actor;
train or derive a new residual head with feature_dim=128;
reuse the same actor input contract;
run exact before/after split metrics first;
use exact holdout non-regression before any replay;
keep M568/M761 results as diagnostic lineage only;
block PPO and promotion.
```

## Supported Claims

M907 supports:

```text
1. M906 failed for internal actor-feature compatibility, not forbidden input.
2. M399 and M568 share the same P0 human-view 72-dim observation contract.
3. The M761 residual head is M568-feature-specific and should not be adapted by
   padding/truncation.
4. Public-base integration should continue only through a 128-dim public-base
   residual-head design.
```

## Unsupported Claims

M907 does not support:

```text
public-base objective update feasibility;
public-base exact loss improvement;
public-base replay retention;
PPO safety;
checkpoint promotion;
M761 residual transferability to M399.
```

## Decision

Decision:

```text
public_base_feature_dim_compatibility_route_to_128dim_residual_design
```

Next:

```text
m908-v4-public-base-compatible-residual-head-probe-design
```

M908 should be design-only. It should define a public-base-compatible
objective-only residual probe rooted at M399, with a 128-dim residual head and
exact holdout gates before any replay, PPO, or promotion.
