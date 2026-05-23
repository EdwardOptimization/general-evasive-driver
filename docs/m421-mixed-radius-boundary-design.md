# M421 Mixed-Radius Boundary Design

M421 is a design milestone after the M420 radius projection probe. It does not
run projection, PPO, promotion, threshold changes, or actor-input changes.

## M420 Boundary

M420 produced the intended bracket:

| Candidate | Proof | Recovery retained vs M406 |
| --- | --- | ---: |
| medium radius | M267/M264 pass, old-key `39/40` | `0.143419` |
| conservative radius | M267/M264, old-key, M183/M170 pass | `0.115403` |

The medium profile has only one old-key compact failure:

```text
10023|perturbed|12|12|11.000000|-0.800000|1.200000
```

This row is not one of the old-key normal-margin recovery targets. The recovery
targets from M398 are:

```text
9958|perturbed|39|36|9.500000|-1.200000|0.900000
10004|perturbed|31|31|9.500000|-1.000000|0.800000
```

So the right response is not global tightening. Global tightening repairs
`10023` but costs utility everywhere. The next candidate should tighten only
the active `10023` boundary and allow more slack on rows that did not fail.

## Mixed Profiles

Use the M419 active-set v2 sources:

| Source | Conservative | Medium | Loose |
| --- | ---: | ---: | ---: |
| M267 rows `6` and `15` | `0.00015` | `0.00030` | `0.00045` |
| old-key `10004` | `0.00035` | `0.00050` | `0.00065` |
| old-key `9998` | `0.00008` | `0.00012` | `0.00018` |
| old-key `10023` | `0.00020` | `0.00035` | `0.00050` |
| old-key spillover guards | `0.00008` | `0.00015` | `0.00025` |

Define three mixed profiles:

| Profile | M267 rows | `10004` | `9998` | `10023` | spillovers | Purpose |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `mixed_a` | medium | medium | medium | conservative | medium | test whether only tightening `10023` fixes proof while keeping medium utility |
| `mixed_b` | medium | loose | medium | conservative | medium | allow more recovery movement on the M398 `10004` recovery target |
| `mixed_c` | loose | loose | medium | conservative | medium | last bounded attempt to recover utility while keeping the known old-key boundary tight |

Do not loosen `9998` yet. It had a narrow pass/fail action-distance gap in
M417 and should remain at medium unless a later audit shows it is blocking
utility.

Do not loosen `10023` unless the old-key compact replay result has a new
separate guard. M420 directly identifies it as the medium proof failure.

## Probe Order

M422 should export these mixed profiles and run no-update exact repair smokes.
M423 should run no-PPO projection in this order:

```text
mixed_a
if proof passes and recovery >= 0.20: full public gate candidate
if proof passes and 0.15 <= recovery < 0.20: run mixed_b
if mixed_b proof passes and recovery < 0.20: run mixed_c
if any profile fails proof: stop and audit the newly active row
```

This keeps M420's primary threshold unchanged:

```text
recovery improvement retained vs M406 >= 0.20
```

The `0.15` value is not a promotion threshold. It is only a branching threshold
to decide whether a proof-passing mixed profile is close enough to justify a
more permissive follow-up profile.

## Acceptance Criteria For The Future Probe

Primary pass:

```text
exact M297/M270/old-key no-regression
M267/M264 first replay: 17 / 17 success drops
old-key compact replay: 0 accepted regressions
M183/M170 first replay: 17 / 17 success drops
recovery improvement retained vs M406 >= 0.20
```

Partial evidence:

```text
all proof gates pass
0.15 <= recovery improvement retained vs M406 < 0.20
```

Partial evidence is not promotable. It can only admit another radius/profile
design or utility audit.

## Forbidden Shortcuts

- Do not lower exact, M267/M264, old-key, M183/M170, or recovery thresholds.
- Do not run PPO before a no-PPO mixed-radius projection passes primary
  criteria.
- Do not change actor inputs or outputs.
- Do not make replay labels actor inputs.

## Decision

Admit:

```text
m422-mixed-radius-anchor-export-implementation
```

M422 should export `mixed_a`, `mixed_b`, and `mixed_c` anchors and run
no-update exact repair smokes only. The projection probe should be M423.
