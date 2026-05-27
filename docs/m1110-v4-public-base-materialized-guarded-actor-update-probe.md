# M1110 V4 Public Base Materialized Guarded Actor Update Probe

## Purpose

M1110 runs the bounded actor-coupling update probe designed in M1109.

This milestone runs only `outcome_intervention_optimize` candidates and an exact
M1107 objective evaluation. It does not run PPO, replay, corpus build, mining,
promotion, private holdout, or actor-input changes.

## Setup

Base checkpoint:

```text
runs/m1073_medium_ppo_failed_row_repair_projection_probe/temporal_projection/checkpoints/m1031_base_row16x4_s40_a1.pt
```

Materialized objective corpus:

```text
runs/m1107_materialized_objective_corpus/boundary_outcome_corpus.npz
```

Recipe:

```text
seeds: 110900, 110901, 110902
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

All three candidates improve the sampled optimizer-side M1107 objective:

| Candidate | Sampled before loss | Sampled after loss | Improvement | Action-anchor MSE | Snippet-anchor MSE |
| --- | ---: | ---: | ---: | ---: | ---: |
| `m1110_110900` | 0.681908 | 0.677021 | 0.004887 | 0.000015001 | 0.000024337 |
| `m1110_110901` | 0.681908 | 0.676896 | 0.005012 | 0.000014091 | 0.000026501 |
| `m1110_110902` | 0.681908 | 0.676905 | 0.005003 | 0.000013565 | 0.000026855 |

All anchor MSE values are below the pre-registered `0.0001` threshold.

## Exact M1107 Objective

Artifact:

```text
runs/m1110_materialized_actor_update_exact_eval/summary.json
```

Exact full-corpus losses:

| Policy | Exact loss | Delta vs base |
| --- | ---: | ---: |
| `proof_current` | 0.679117 | 0.000000 |
| `m1110_110900` | 0.674470 | -0.004647 |
| `m1110_110901` | 0.674349 | -0.004768 |
| `m1110_110902` | 0.674359 | -0.004758 |

All three candidates improve the exact objective. The lowest exact loss is
`m1110_110901`.

## Parameter-Scope Audit

Each candidate changes exactly these tensors:

```text
response_context_fusion.0.weight
response_context_fusion.0.bias
actor_mean.weight
actor_mean.bias
```

No candidate changes `log_std`, response encoder, context encoder, GRU, critic,
or actor-input contract metadata.

| Candidate | Changed tensors | Disallowed tensors | log_std changed | Max abs delta |
| --- | ---: | ---: | --- | ---: |
| `m1110_110900` | 4 | 0 | false | 0.000480935 |
| `m1110_110901` | 4 | 0 | false | 0.000488654 |
| `m1110_110902` | 4 | 0 | false | 0.000484020 |

## Interpretation

M1110 is a positive exact/contract candidate probe:

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
result only admits a full public gate design for the primary candidate
`m1110_110901`.

## Decision

```text
materialized_guarded_actor_update_exact_candidate_route_to_full_public_gate_design
```

Primary candidate for the next gate design:

```text
runs/m1110_materialized_actor_coupling_anchor100_s10_lr5e5_seed110901/optimized_checkpoint.pt
```

Next milestone:

```text
m1111-v4-public-base-materialized-actor-update-full-public-gate-design
```
