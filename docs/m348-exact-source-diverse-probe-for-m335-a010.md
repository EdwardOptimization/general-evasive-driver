# M348 Exact Source-Diverse Probe For M335 A010

M348 probes the largest old-key-neighborhood-passing M335 interpolation
candidate from M347:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

No PPO, actor update, promotion, or actor-input change was performed.

## Lineage

Current public-gate base:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt
```

Candidate:

```text
runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt
```

M347 already established that `alpha=0.01` is the largest M335 interpolation
alpha passing the replayable old-key neighborhood gate, while `alpha=0.02` is
the first failing alpha.

## Exact Objectives

Run dir:

```text
runs/m348_m335_a010_exact_eval_vs_a0075
```

Exact objective retention versus the current M336 public base:

| Objective | Candidate loss | Delta vs base | Pass |
| --- | ---: | ---: | --- |
| Exact M297 rejected-history preference | 1.189185143 | -0.000000954 | true |
| Exact M270 source-balanced outcome | 0.677674532 | -0.000000477 | true |

Both exact objectives pass no-regression.

## Source-Diverse Protected Gate

Run dir:

```text
runs/m348_m335_a010_source_diverse_protected_gate
```

All five source-diverse protected replay gates pass.

| Replay gate | Rows | Baseline drops | Candidate drops | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| current_m333_surface | 17 | 17 | 17 | +0.000005535 | +0.000003428 | true |
| m328_continuity_surface | 17 | 17 | 17 | +0.000096173 | +0.000041158 | true |
| m325_continuity_surface | 17 | 17 | 17 | +0.000290007 | +0.000126035 | true |
| m317_continuity_surface | 17 | 17 | 17 | +0.000484801 | +0.000206280 | true |
| m314_continuity_surface | 17 | 17 | 17 | +0.000485323 | +0.000206479 | true |

## Old-Key Neighborhood Gate

M348 reuses the M347 targeted replay and replayable old-key neighborhood gate
result:

```text
runs/m347_old_key_alpha_sweep/summary.json
```

| Policy | Alpha | Pass | Accepted regressions | Normal-success regressions | Gap p10 | Gap min |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| m335_a010 | 0.01 | true | 0 | 0 | -0.000006 | -0.000016 |
| m335_a020 | 0.02 | false | 1 | 0 | -0.000030 | -0.000082 |

This keeps the old `9944` singleton visible through the M341 compact
neighborhood, but no longer lets a single stale row dominate acceptance.

## First Replay Gates

M348 runs the two first replay gates required before a full public gate.

| Surface | Rows | Success drops retained | Normal margin delta | Margin gap delta | Pass |
| --- | ---: | ---: | ---: | ---: | --- |
| M183/M170 | 17 | 17 / 17 | +0.000006544 | +0.000001179 | true |
| M267/M264 | 17 | 17 / 17 | +0.000005530 | +0.000003428 | true |

Run dirs:

```text
runs/m348_m335_a010_m183_m170_first_replay
runs/m348_m335_a010_m267_m264_first_replay
```

## Interpretation

M348 is positive as a proof-gate probe. The `m335_a010` candidate preserves the
exact objectives versus the current M336 base, passes the source-diverse
protected gate, retains the M347 old-key neighborhood result, and passes the
first replay gates.

This is not a promotion. It only says `m335_a010` is eligible for a full public
gate. The remaining question is whether it also retains all six public replay
surfaces and public behavior seeds.

## Decision

Decision:

```text
admit_m349_full_public_gate_for_m335_a010
```

Next:

```text
m349-full-public-gate-for-m335-a010
```
