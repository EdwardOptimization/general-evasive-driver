# M241 Trajectory PPO Seed Direction Audit

M241 audits why M237 produced a useful interpolation-guarded direction while
M240 did not. No PPO is run in this milestone.

Actor inputs are unchanged.

## Question

M239 showed that interpolation can rescue a useful PPO update direction:

```text
M224 -> M237 raw -> alpha 0.5 = public-gate base
```

M240 repeated the same recipe on a fresh seed:

```text
M224 -> M240 raw -> alpha 0.5
```

The repeat preserved proof and behavior, but did not improve the combined M232
objective. M241 checks whether this is proof-retention fragility, objective
direction fragility, or metric noise.

## Deterministic Full-Corpus Objective

The previous fixed-batch objective evaluator samples many batches from a very
small corpus. M232 has 18 rows and M223 has 17 rows, so tiny differences should
be checked with a deterministic full-corpus calculation.

Exact M232 loss:

| Policy | Loss | Delta vs M224 |
| --- | ---: | ---: |
| m224 | 0.244663030 | 0.000000000 |
| m237_raw | 0.244636327 | -0.000026703 |
| m239_a500 | 0.244649455 | -0.000013575 |
| m240_raw | 0.244676247 | 0.000013217 |
| m240_a500 | 0.244669333 | 0.000006303 |

Exact M223 loss:

| Policy | Loss | Delta vs M224 |
| --- | ---: | ---: |
| m224 | 0.209025383 | 0.000000000 |
| m237_raw | 0.208989084 | -0.000036299 |
| m239_a500 | 0.209007069 | -0.000018314 |
| m240_raw | 0.209021538 | -0.000003845 |
| m240_a500 | 0.209023222 | -0.000002161 |

This confirms the sampled fixed-batch result:

- M237 improves M232 and M223.
- M239 keeps part of that improvement.
- M240 improves M223 only marginally but regresses M232.

The M240 issue is not a false sampled-batch artifact.

## Retention Comparison

M239 and M240 both show that interpolation can preserve proof retention.

| Milestone | Candidate | M183 M170 | Protected key | Full replay | Behavior |
| --- | --- | --- | --- | --- | --- |
| M239 | alpha 0.5 | pass | pass | pass | 0.8625 |
| M240 | alpha 0.5 | pass | pass | pass | 0.8625 |

M240 even improves the M183 M170 row-16 margin relative to M224:

```text
M224 row16 margin:      0.000106
M239 alpha0.5 margin:   0.000008
M240 alpha0.5 margin:   0.000359
```

So the blocker has moved: the current interpolation guard can retain proof, but
the PPO update direction does not reliably improve the combined objective that
now includes the protected key.

## Diagnosis

Best classification:

```text
seed-fragile PPO objective direction under very small fixed-objective deltas
```

The deltas are on the order of `1e-5`. That is enough to choose between public
proof-gated candidates only if the objective is deterministic and full-corpus.
Using sampled fixed-batch numbers as the primary promotion signal is too weak at
this scale.

Failure taxonomy:

```text
seed_fragility
metric_artifact
promotion_gate_failure
```

`metric_artifact` here means the workflow needs a stricter deterministic metric
for small corpora before more PPO decisions. It does not mean M240's regression
was false; the exact metric confirms it.

## Decision

Keep current public-gate base:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Do not run more PPO until the exact objective evaluator is part of the harness.

Next step:

```text
m242-exact-outcome-objective-evaluator
```

M242 should add a deterministic full-corpus outcome objective evaluator and
tests, then future PPO/interpolation promotion gates should use it alongside
proof and behavior gates.
