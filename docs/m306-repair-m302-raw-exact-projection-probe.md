# M306 Repair M302 Raw Exact Projection Probe

M306 tests whether the rejected M302 raw PPO proposal can be repaired by exact
full-corpus projection before replay gates. No PPO was run, actor inputs are
unchanged, and no checkpoint is promoted in this milestone.

## Candidate Generation

Base:

```text
runs/m298_rejected_preference_objective_only_probe/interpolation/checkpoints/alpha_0_02.pt
```

Rejected raw PPO proposal:

```text
runs/ppo_m302_rejected_preference_guarded_smoke_seed5233/checkpoint.pt
```

Repair tool:

```text
python -m autodrift.exact_post_ppo_repair
```

Three exact repair candidates were generated with `40` actor-coupling steps,
`lr=5e-6`, exact M297/M270 hinge penalties, M299 action anchor, M299 parameter
trust region, and a small raw-proposal pull term:

| Candidate | Start | Checkpoint | Exact M297 delta | Exact M270 delta | Exact pass |
| --- | --- | --- | ---: | ---: | --- |
| raw_s40 | M302 raw | `runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt` | -0.000126243 | -0.000080407 | true |
| base_s40 | M299 base | `runs/m306_exact_repair_from_base_s40_seed10092/candidate_checkpoint.pt` | -0.000074863 | -0.000041604 | true |
| line_boundary_s40 | line-search alpha 0.0 | `runs/m306_exact_repair_line_boundary_s40_seed10093/candidate_checkpoint.pt` | -0.000074863 | -0.000041604 | true |

The raw-start candidate has the strongest exact-objective improvement, so it
was selected for first replay gates.

## First Replay Gates

Selected candidate:

```text
runs/m306_exact_repair_from_raw_s40_seed10091/candidate_checkpoint.pt
```

### M183/M170

Run dir:

```text
runs/m306_raw_s40_m183_m170_first_replay
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
runs/m306_raw_s40_m267_m264_first_replay
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

M306 is a qualified positive. The exact post-PPO projection can turn the
rejected M302 raw proposal into an exact-passing candidate that retains the two
first replay surfaces.

This is not yet a promotion:

- full replay stack was not run;
- protected-key diagnostic was not run;
- behavior seeds `9505` and `9506` were not run;
- private holdout is not used.

The result is enough to admit a full public-gate check for the selected
candidate.

## Decision

Admit:

```text
m307-full-public-gate-for-m306-raw-s40
```

Decision:

```text
admit_m307_full_public_gate_for_m306_raw_s40
```
