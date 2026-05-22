# M243 Exact-Gated PPO Smoke From M239

M243 runs exactly one 1024-step PPO smoke from the M239 public-gate base, then
evaluates a post-PPO interpolation sweep with the new exact full-corpus objective
gate. The milestone stops at the objective gate because every alpha regresses
the combined M232 objective.

Actor inputs are unchanged.

## Setup

Initial checkpoint:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Config:

```text
configs/ppo_m243_exact_gated_from_m239_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m243_exact_gated_from_m239_seed5223/checkpoint.pt
```

Interpolation sweep:

```text
runs/m243_m239_to_raw_interpolation
```

## Raw PPO Training

Training metrics:

| Step | Rollout return mean | Reward mean | Episodes | Built-in eval termination | Outcome loss | Baseline anchor loss | Snippet anchor loss | Trajectory anchor loss |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1024 | 54.049 | 0.917 | 10 | 0.2000 | 0.253416 | 0.0000110 | 0.000000044 | 0.000000232 |

The smoke completed, but rollout quality was weaker than the recent M237/M240
smokes and the raw training rollout termination was `0.4`.

## Exact Objective Gate

M232 combined objective:

| Policy | Alpha | Exact loss | Delta vs M239 |
| --- | ---: | ---: | ---: |
| m239_a500 | 0.00 | 0.244649454951 | 0.000000000000 |
| m243_a100 | 0.10 | 0.244649633765 | 0.000000178814 |
| m243_a250 | 0.25 | 0.244650021195 | 0.000000566244 |
| m243_a500 | 0.50 | 0.244650721550 | 0.000001266599 |
| m243_a750 | 0.75 | 0.244651511312 | 0.000002056360 |
| m243_a1000 | 1.00 | 0.244652479887 | 0.000003024936 |

M223 objective:

| Policy | Alpha | Exact loss | Delta vs M239 |
| --- | ---: | ---: | ---: |
| m239_a500 | 0.00 | 0.209007069468 | 0.000000000000 |
| m243_a100 | 0.10 | 0.209006235003 | -0.000000834465 |
| m243_a250 | 0.25 | 0.209005072713 | -0.000001996756 |
| m243_a500 | 0.50 | 0.209003180265 | -0.000003889203 |
| m243_a750 | 0.75 | 0.209001347423 | -0.000005722046 |
| m243_a1000 | 1.00 | 0.208999633789 | -0.000007435679 |

This is an objective conflict:

- the update improves the old M223 surface;
- the update regresses the combined M232 surface that includes the protected key.

M243 did not pre-register a tolerance for positive M232 drift. Therefore even
the tiny `alpha=0.1` M232 regression is not promoted.

## Proof Gates

Proof and behavior gates were not run. The candidate failed before reaching
that stage:

```text
exact M232 objective gate failed for every alpha
```

## Diagnosis

M243 confirms that exact objective gating is useful: it stops a candidate that
would likely have looked acceptable under a looser M223-only view.

The likely issue is a protected-key/objective conflict inside M232:

```text
17 M223 rows improve, but the protected-key row worsens enough to move M232 up.
```

Failure taxonomy:

```text
objective_overfit
promotion_gate_failure
```

## Decision

M243 is rejected.

Current public-gate base remains:

```text
runs/m239_m224_to_m237_interpolation/checkpoints/alpha_0_5.pt
```

Next step:

```text
m244-m243-protected-key-objective-conflict-audit
```

M244 should compute per-row and per-source exact objective movement for M239 to
M243, especially the M231 protected-key row versus the M223 rows, before any
more PPO.
