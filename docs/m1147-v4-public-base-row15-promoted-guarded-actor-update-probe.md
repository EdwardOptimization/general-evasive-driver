# M1147 V4 Public Base Row15 Promoted Guarded Actor Update Probe

## Purpose

M1147 runs the bounded actor-coupling update probe designed in M1146.

This milestone runs only `outcome_intervention_optimize` candidates plus exact
M1144 objective evaluation and parameter-scope audit. It does not run PPO,
replay, corpus build, objective sanity, mining, promotion, private holdout, or
actor-input changes.

## Setup

Base checkpoint:

```text
runs/m1123_row15_unsafe_margin_projection_probe/checkpoints/alpha_0_15.pt
```

Materialized objective corpus:

```text
runs/m1144_row15_promoted_objective_corpus/boundary_outcome_corpus.npz
```

Recipe:

```text
seeds: 114600, 114601, 114602
steps: 10
learning_rate: 0.00005
batch_size: 64
train_scope: actor_coupling
freeze_log_std: true
action_anchor_coef: 100.0
snippet_action_anchor_coef: 100.0
snippet_action_anchor_include_rejected_hidden: true
grad_clip_norm: 0.5
```

## Optimizer Results

All three candidates improve the sampled optimizer-side M1144 objective:

| Candidate | Sampled before loss | Sampled after loss | Improvement | Action-anchor MSE | Snippet-anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m1147_114600` | 0.383050 | 0.376167 | 0.006883 | 0.000007831 | 0.000018473 |
| `m1147_114601` | 0.383050 | 0.376170 | 0.006880 | 0.000007962 | 0.000018814 |
| `m1147_114602` | 0.383050 | 0.376041 | 0.007009 | 0.000008367 | 0.000019765 |

All anchor MSE values are below the pre-registered `0.0001` threshold.

## Exact M1144 Objective

Artifact:

```text
runs/m1147_row15_promoted_actor_update_exact_eval/summary.json
```

Exact full-corpus losses:

| Policy | Exact loss | Delta vs base |
| --- | ---: | ---: |
| `row15_current` | 0.417700 | 0.000000 |
| `m1147_114600` | 0.409554 | -0.008146 |
| `m1147_114601` | 0.409563 | -0.008137 |
| `m1147_114602` | 0.409408 | -0.008292 |

All three candidates improve the exact objective. The lowest exact loss is
`m1147_114602`.

## Parameter-Scope Audit

Artifact:

```text
runs/m1147_row15_promoted_actor_update_parameter_audit/summary.json
```

Each candidate changes exactly these tensors:

```text
actor_mean.bias
actor_mean.weight
response_context_fusion.0.bias
response_context_fusion.0.weight
```

No candidate changes `log_std`, response encoder, context encoder, GRU, critic,
or actor-input contract metadata.

| Candidate | Changed tensors | Disallowed tensors | log_std changed | Max abs delta |
| --- | ---: | ---: | --- | ---: |
| `m1147_114600` | 4 | 0 | false | 0.000490053 |
| `m1147_114601` | 4 | 0 | false | 0.000473611 |
| `m1147_114602` | 4 | 0 | false | 0.000495574 |

## Interpretation

M1147 is a positive exact/contract pre-replay candidate probe:

```text
exact objective improves
anchor drift remains low
parameter movement is contract-clean
actor inputs are unchanged
PPO was not used
private holdout was not used
promotion did not occur
```

This still does not prove closed-loop improvement. No replay has run yet. The
result only admits first replay gate design for the primary candidate
`m1147_114602`.

## Decision

```text
row15_promoted_guarded_actor_update_exact_candidate_route_to_first_replay_design
```

Primary candidate for the next gate design:

```text
runs/m1147_row15_promoted_actor_coupling_anchor100_s10_lr5e5_seed114602/optimized_checkpoint.pt
```

Next milestone:

```text
m1148-v4-public-base-row15-promoted-actor-update-first-replay-design
```
