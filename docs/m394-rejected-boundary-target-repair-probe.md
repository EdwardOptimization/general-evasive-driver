# M394 Rejected-Boundary Target Repair Probe

M394 probes the M393 collision-side rejected-history targets in a no-PPO exact
repair/interpolation loop. It does not promote a checkpoint and does not change
the actor input/output contract.

## Inputs

Current public-gate base:

```text
runs/m390_step17_micro_interpolation/checkpoints/alpha_0_005.pt
```

M393 current-family conflict corpus:

```text
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
```

Selected candidate:

```text
runs/m394_s02_micro_interpolation/checkpoints/alpha_0_1.pt
```

This is `alpha=0.1` from the current base toward the step2 lexicographic repair
direction:

```text
runs/m394_rejected_boundary_target_repair_s02_lexheavy_seed10132/candidate_checkpoint.pt
```

## Repair Search

The first repair endpoint was useful as a direction but not acceptable:

| Candidate | Exact pass | M267/M264 pass | Old-key compact pass | Main failure |
| --- | --- | --- | --- | --- |
| s80 endpoint | true | false | not run | M267/M264 normal branch `0/17` |
| s10 direct | true | false | not run | M267/M264 normal branch `6/17` |
| s05 direct | true | true | false | old-key accepted rows `33/40` |
| s02 direct | true | true | false | old-key accepted rows `34/40` |
| s02 alpha 0.2 | true | not run | false | old-key accepted rows `39/40` |
| s02 alpha 0.1 | true | true | true | selected bounded candidate |

This is another bounded proof-retention move. The important result is that the
new rejected-boundary target direction is usable only inside a small trust
region.

## Exact Gate

Exact eval:

```text
runs/m394_s02a010_exact_eval
```

| Metric | Delta vs M391 base |
| --- | ---: |
| exact M297 | -0.000048637 |
| exact M270 | -0.000028133 |
| old-key surrogate | -0.000130653 |
| current-family conflict loss | 0.006163536 |
| exact lexicographic pass | true |

The conflict loss improvement is intentionally small because old-key compact
rows are the active limiting surface after the current-family row15 repair
direction starts moving.

## Proof Gates

M267/M264 first replay:

```text
runs/m394_s02a010_m267_m264_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | -0.000125861 |
| margin gap delta | +0.000002171 |

Cumulative old-key compact replay:

```text
runs/m394_s02a010_old_key_replay_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| accepted regressions | 0 |
| normal-success regressions | 0 |
| gap p10 | -0.000088914 |
| gap min | -0.000147267 |

Source-diverse protected gate:

```text
runs/m394_s02a010_source_diverse_protected_gate
```

| Metric | Value |
| --- | ---: |
| overall pass | true |
| replay gates passed | 5 / 5 |

M183/M170 first replay:

```text
runs/m394_s02a010_m183_m170_first_replay
```

| Metric | Value |
| --- | ---: |
| gate pass | true |
| success drops retained | 17 / 17 |
| wrong-history success rate | 0 |
| normal margin delta | -0.000133569 |
| margin gap delta | +0.000002216 |

## Interpretation

M394 is a positive proof-gate result, but it is still a micro-step. The M393
collision-side rejected target gives a valid direction, yet direct repair
quickly damages either the normal branch or the old-key compact surface. The
acceptable point is the bounded alpha `0.1` interpolation from the step2
direction.

This candidate should not be promoted from M394 alone. It should enter a full
public gate with all six replay surfaces and behavior seeds.

## Decision

Classify:

```text
bounded_repair_probe_success
```

Admit:

```text
m395-full-public-gate-for-m394-s02a010
```

Decision:

```text
admit_m395_full_public_gate_for_m394_s02a010
```
