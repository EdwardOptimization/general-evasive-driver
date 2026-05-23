# M308 Exact Repair Fresh Seed Repeat

M308 repeats the M306 exact repair projection recipe with a fresh optimizer
seed before starting another PPO proposal. No PPO was run, actor inputs are
unchanged, and no checkpoint is promoted in this milestone.

## Repeat Candidate

Command shape:

```text
python -m autodrift.exact_post_ppo_repair
```

Run dir:

```text
runs/m308_exact_repair_from_raw_s40_seed10094
```

Candidate:

```text
runs/m308_exact_repair_from_raw_s40_seed10094/candidate_checkpoint.pt
```

Exact objective result versus M299:

| Objective | Delta |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000126243 |
| Exact M270 source-balanced outcome | -0.000080407 |

The repeat matches the M306 raw-start result. This is expected because the
M305/M306 repair path is full-batch deterministic; the optimizer seed no
longer changes sampled rows.

## First Replay Gates

### M183/M170

Run dir:

```text
runs/m308_raw_s40_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000211 |
| Margin gap mean delta | +0.000031 |
| Gate pass | true |

### M267/M264

Run dir:

```text
runs/m308_raw_s40_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| Normal success | 1.000000 |
| Wrong-history success | 0.000000 |
| Success drops retained | 17 / 17 |
| Normal margin mean delta | +0.000188 |
| Margin gap mean delta | +0.000077 |
| Gate pass | true |

## Interpretation

The exact repair projection recipe is deterministic and repeat-stable for the
current M302 proposal. This removes optimizer seed fragility as the immediate
blocker.

The remaining risk is PPO proposal direction, not repair optimizer seed. The
next milestone should design a fresh PPO proposal from the M307 public-gate
base and route that proposal through the exact repair gate before any replay or
promotion decision.

## Decision

Admit:

```text
m309-exact-repaired-ppo-proposal-design
```

Decision:

```text
admit_exact_repaired_ppo_proposal_design
```
