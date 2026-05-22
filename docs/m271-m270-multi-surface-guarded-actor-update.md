# M271 M270 Multi-Surface Guarded Actor Update

M271 runs exactly one small actor update from `m264_a001` using the M270
source-balanced multi-surface corpus.

No PPO, repeat seed, promotion, or actor-input change was performed.

## Setup

Initial checkpoint:

```text
runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Snippet corpus:

```text
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

Recipe:

```text
steps = 10
learning_rate = 0.00005
train_scope = actor_coupling
action_anchor_coef = 100
snippet_action_anchor_coef = 100
snippet_action_anchor_preferred_only = true
```

## Actor Update

Artifact:

```text
runs/m271_m264_actor_coupling_m270_multisurface_anchor100_s10_lr5e5_seed10074/optimized_checkpoint.pt
```

| Metric | Value |
| --- | ---: |
| before eval loss mean | 0.680906 |
| after eval loss mean | 0.674150 |
| loss improvement | 0.006757 |
| after action anchor MSE | 0.000016788 |
| after snippet action anchor MSE | 0.000029965 |
| objective sanity pass | true |

## Fixed M270 Eval

Artifacts:

- `runs/m271_fixed_batch_outcome_eval_seed37`
- `runs/m271_exact_outcome_eval_seed37`

| Policy | Sampled M270 loss | Exact M270 loss |
| --- | ---: | ---: |
| `m264_a001` | 0.681606 | 0.681443 |
| `m271_10074` | 0.674872 | 0.674680 |

M271 improves the combined M270 objective under both sampled fixed-batch and
exact full-corpus evaluation.

## Replay Gates

Replay gates compare M271 against the source policy for each corpus. Since proof
gates fail, behavior and protected-key diagnostic gates are not run.

| Corpus | Rows | Candidate normal success | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 0.1875 | 3 / 16 | -0.007087 | 0.001199 | false |
| M183 M170 | 17 | 0.176471 | 3 / 17 | -0.007428 | 0.001077 | false |
| M193 M189 | 14 | 0.357143 | 5 / 14 | -0.005975 | 0.000514 | false |
| M212 M204 | 17 | 0.411765 | 7 / 17 | -0.005029 | -0.000093 | false |
| M223 M219 | 17 | 0.882353 | 15 / 17 | -0.004466 | -0.000359 | false |
| M267 M264 | 17 | 1.0000 | 17 / 17 | -0.002787 | 0.000061 | true |

M271 retains only the current M267 surface. The combined corpus improves the
training objective but still does not preserve closed-loop normal success across
older and intermediate proof surfaces.

## Failure Classification

```text
proof_washout
objective_overfit
```

M271 is more informative than M268:

- M268 showed M267-only anchoring could not protect old M183/M193 surfaces;
- M270 added source-balanced old/current/protected rows;
- M271 still washes out old surfaces and now also weakens M212/M223.

This points to step size / closed-loop trajectory drift rather than simple row
coverage. The next check should not be another update seed. It should be a
no-training interpolation probe from `m264_a001` toward the M271 checkpoint.

## Decision

M271 is rejected.

What it proves:

- the combined M270 objective is steerable;
- source-balanced snippets alone are still insufficient at full update size;
- proof gates must remain before behavior, protected-key, or promotion gates.

What it does not prove:

- that a smaller interpolation cannot retain proof while improving objective;
- that trajectory anchors would fail;
- that PPO can continue.

Decision:

```text
reject_multi_surface_actor_update_proof_washout
```

Next step:

```text
m272-m271-interpolation-retention-probe
```

M272 should perform a no-training interpolation sweep from `m264_a001` toward
`m271_10074`, then gate exact/fixed M270 objective and replay surfaces before
any repeat update or PPO.
