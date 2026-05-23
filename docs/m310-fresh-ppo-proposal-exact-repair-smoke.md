# M310 Fresh PPO Proposal Exact Repair Smoke

M310 runs one fresh smoke-scale PPO proposal from the M307 public-gate base and
accepts it only through exact post-PPO repair. Actor inputs are unchanged.

## Raw PPO Proposal

Initial checkpoint:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

Config:

```text
configs/ppo_m310_exact_repaired_proposal_smoke.json
```

Raw PPO checkpoint:

```text
runs/ppo_m310_exact_repaired_proposal_smoke_seed5234/checkpoint.pt
```

Smoke result:

| Metric | Value |
| --- | ---: |
| rollout_return_mean | 68.795477 |
| reward_mean | 1.042794 |
| episode_count | 11 |
| episode_length_mean | 64.363636 |
| termination_rate | 0.181818 |
| rejected_history_preference_loss_mean | 1.106377 |

The raw PPO checkpoint is not promotable. Exact evaluation shows the same class
of regression as M302:

| Policy | Exact M297 | Exact M270 |
| --- | ---: | ---: |
| M307 base | 1.189483285 | 0.677865505 |
| M310 raw PPO | 1.190135360 | 0.678286314 |
| Raw delta | +0.000652075 | +0.000420809 |

## Exact Repair

Repair run:

```text
runs/m310_exact_repair_from_raw_s40_seed10095
```

Candidate:

```text
runs/m310_exact_repair_from_raw_s40_seed10095/candidate_checkpoint.pt
```

Exact repair result versus M307:

| Policy | Exact M297 | Exact M270 |
| --- | ---: | ---: |
| M307 base | 1.189483285 | 0.677865505 |
| M310 repaired | 1.189360261 | 0.677787662 |
| Repaired delta | -0.000123024 | -0.000077844 |

The repaired candidate passes the exact lexicographic gate.

## First Replay Gates

### M183/M170

Run dir:

```text
runs/m310_repaired_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000207 |
| Margin gap mean delta | +0.000030 |
| Gate pass | true |

### M267/M264

Run dir:

```text
runs/m310_repaired_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000184 |
| Margin gap mean delta | +0.000080 |
| Gate pass | true |

## Interpretation

M310 is positive as a proof-stage PPO proposal. Raw PPO still regresses the
exact full-corpus objectives, so the M303 conclusion remains valid: sampled PPO
metrics are not promotion gates.

The exact post-PPO repair step restores and improves both exact objectives
versus M307, then preserves the first replay surfaces. This supports the
current workflow:

```text
PPO = proposal
exact repair = feasibility restoration
replay gates = closed-loop proof retention
```

M310 is not promoted because only first replay gates were run. It admits a
separate full public-gate milestone.

## Decision

Admit:

```text
m311-full-public-gate-for-m310-repaired-ppo-proposal
```

Decision:

```text
admit_m311_full_public_gate_for_m310_repaired_ppo_proposal
```
