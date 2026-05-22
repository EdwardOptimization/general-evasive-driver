# M268 M267 Guarded Actor Update From M264

M268 runs exactly one small guarded actor update from `m264_a001` using the
M267 M264 protected-surface corpus.

No PPO, repeat seed, promotion, or actor-input change was performed.

## Setup

Initial checkpoint:

```text
runs/m264_m263_to_raw_interpolation/checkpoints/alpha_0_001.pt
```

Snippet corpus:

```text
runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.npz
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

This mirrors the small M216/M224 actor-update recipe, adapted to the refreshed
M267 protected-surface corpus and the M264 public-gate base.

## Actor Update

Artifact:

```text
runs/m268_m264_actor_coupling_m267_snippet_pref_anchor100_s10_lr5e5_seed10073/optimized_checkpoint.pt
```

| Metric | Value |
| --- | ---: |
| before eval loss mean | 0.213530 |
| after eval loss mean | 0.212334 |
| loss improvement | 0.001197 |
| after action anchor MSE | 0.000005688 |
| after snippet action anchor MSE | 0.000002992 |
| objective sanity pass | true |

## Fixed M267 Eval

Artifacts:

- `runs/m268_fixed_batch_outcome_eval_seed37`
- `runs/m268_exact_outcome_eval_seed37`

| Policy | Sampled M267 loss | Exact M267 loss |
| --- | ---: | ---: |
| `m264_a001` | 0.213681 | 0.212996 |
| `m268_10073` | 0.212479 | 0.211805 |

M268 improves the M267 objective under both sampled fixed-batch and exact
full-corpus evaluation.

## Replay Gates

Replay gates compare M268 against the source policy for each corpus. Proof gates
are evaluated before behavior and protected-key gates.

| Corpus | Rows | Candidate normal success | Candidate drops | Normal margin delta | Margin gap delta | Gate pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 0.1875 | 3 / 16 | -0.006228 | 0.001148 | false |
| M183 M170 | 17 | 0.176471 | 3 / 17 | -0.006575 | 0.001027 | false |
| M193 M189 | 14 | 0.357143 | 5 / 14 | -0.005204 | 0.001181 | false |
| M212 M204 | 17 | 1.0000 | 17 / 17 | -0.004233 | 0.000450 | true |
| M223 M219 | 17 | 1.0000 | 17 / 17 | -0.003670 | 0.000185 | true |
| M267 M264 | 17 | 1.0000 | 17 / 17 | -0.001991 | 0.000041 | true |

M268 retains the recent M212/M223/M267 surfaces, but washes out old M183 and
M193 proof surfaces. Since proof gates failed, behavior and old protected-key
diagnostic gates were not run.

## Failure Classification

```text
proof_washout
objective_overfit
```

M268 is a useful negative result: optimizing the new M267 protected surface with
only action/snippet anchors can improve the intended objective while breaking
older proof surfaces. The failure is not lack of M267 objective steerability; it
is insufficient multi-surface retention.

## Decision

M268 is rejected.

What it proves:

- the M267 objective is steerable from `m264_a001`;
- the small preferred-only actor update is not safe when anchored only by M267
  and generic action samples;
- proof gates must remain layered before behavior and promotion gates.

What it does not prove:

- that actor updates from M264 are impossible;
- that M267 should be discarded;
- that PPO can continue.

Decision:

```text
reject_actor_update_proof_washout
```

Next step:

```text
m269-m268-old-surface-proof-washout-audit
```

M269 should audit why M268 loses old M183/M193 normal-success rows and decide
whether the next repair needs combined old+new snippet anchors, trajectory
anchors, or a stricter multi-surface objective before any repeat actor update or
PPO.
