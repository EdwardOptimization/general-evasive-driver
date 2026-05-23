# M418 Active-Set Radius Calibration Design

M418 is a design milestone. It does not run PPO, promote a checkpoint, lower
proof thresholds, or change actor inputs.

## M417 Diagnosis

M417 bracketed the remaining active-set tradeoff:

| Variant | Proof | Recovery utility |
| --- | --- | ---: |
| `lambda_replay=1e12`, zero radius | fails M267/M264 `15/17` and old-key `35/40` | `0.226007` of M406 |
| `lambda_replay=1e13`, zero radius | passes M267/M264, old-key, and M183/M170 | `0.054387` of M406 |

So the next variable should not be another scalar lambda. The correct control
knob is the per-row hinge radius that M416 added.

Interpretation:

```text
high lambda + zero radius  -> proof safe, retention heavy
low lambda  + zero radius  -> utility retained, proof failed
high lambda + radius slack -> allow bounded recovery movement, clamp proof rows
```

## Measured Action-Distance Bracket

Distance is RMS action distance from the active-set reference action:

```text
sqrt(mean((policy_action - reference_action)^2))
```

| Source | M417 `1e13` mean | M417 `1e13` p90 | M417 `1e13` max | M417 `1e12` mean | M417 `1e12` p90 | M417 `1e12` max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| M267 row `6` | `0.000065` | `0.000085` | `0.000086` | `0.000578` | `0.000670` | `0.000673` |
| M267 row `15` | `0.000069` | `0.000085` | `0.000086` | `0.000590` | `0.000670` | `0.000672` |
| old-key `10004...0.800000` | `0.000199` | `0.000447` | `0.000552` | `0.001038` | `0.002191` | `0.002617` |
| old-key `9998...1.400000` | `0.000040` | `0.000067` | `0.000134` | `0.000207` | `0.000459` | `0.001005` |
| old-key `10023...1.200000` | `0.000111` | `0.000202` | `0.000339` | `0.000687` | `0.001113` | `0.001687` |

The useful radius interval should sit above the proof-passing `1e13` action
distance but below the proof-failing `1e12` action distance. For narrow-gap rows
like old-key `9998`, the radius must stay close to the `1e13` upper tail.

## Active Set V2

Keep the M416 active rows:

| Source | Role |
| --- | --- |
| M267/M264 row `6` | active wrong-history failure |
| M267/M264 row `15` | active wrong-history failure |
| old-key `10004|perturbed|31|31|9.500000|-1.000000|0.800000` | active wrong-history failure |
| old-key `9998|perturbed|25|25|11.000000|-1.000000|1.400000` | active wrong-history failure |
| old-key `10023|perturbed|12|12|11.000000|-0.800000|1.200000` | active guard, failed at M417 `1e12` |

Add M417 spillover rows as guard rows:

| Source | Role | Why |
| --- | --- | --- |
| old-key `9951|perturbed|35|32|10.000000|-1.200000|1.400000` | spillover guard | M417 `1e12` wrong-history became successful |
| old-key `9939|perturbed|27|27|12.500000|-0.800000|1.400000` | spillover guard | M417 `1e12` wrong-history became successful |

The spillover rows are important because M417 `1e12` failed not only the rows
that were explicitly anchored. Radius calibration should therefore constrain
both active failures and first spillover failures.

## Radius Profiles

M419 should export three radius-calibrated active-set anchors, all with
`lambda_replay_trajectory_anchor=1e13` in the later probe.

| Source group | Conservative | Medium | Loose |
| --- | ---: | ---: | ---: |
| M267 rows `6` and `15` | `0.00015` | `0.00030` | `0.00045` |
| old-key `10004` | `0.00035` | `0.00050` | `0.00065` |
| old-key `9998` | `0.00008` | `0.00012` | `0.00018` |
| old-key `10023` | `0.00020` | `0.00035` | `0.00050` |
| old-key spillover guards | `0.00008` | `0.00015` | `0.00025` |

The intended first probe order is:

```text
medium -> conservative -> loose
```

Run `medium` first because it is the smallest profile likely to improve over
the M417 `1e13` utility collapse while staying well below the M417 `1e12`
failure distances for M267 rows. Run `conservative` if medium fails proof. Run
`loose` only if medium passes proof but still has poor recovery retention.

## M419 Implementation Scope

M419 should implement/export radius-calibrated anchors only:

1. Add or reuse an anchor-export path that can write explicit per-row `radius`.
2. Export active-set v2 with the five M416 rows plus the two M417 spillover
   old-key rows.
3. Produce three NPZs:
   - `conservative_radius_anchor.npz`
   - `medium_radius_anchor.npz`
   - `loose_radius_anchor.npz`
4. Save a CSV with source, role, rows, radius, and weight.
5. Run no-update exact repair smokes for all three anchors.
6. Do not run any projection, PPO, or promotion.

## M420 Probe Design

M420 should run the no-PPO projection probe using the radius anchors from M419.

Fixed settings:

```text
base checkpoint: runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
raw checkpoint:  runs/m403_lrec1e10_interpolation/checkpoints/alpha_0_1.pt
lambda_replay_trajectory_anchor: 1e13
exact M297/M270/old-key gates: no-regression
```

Probe order:

```text
medium radius
if proof fails: conservative radius
if proof passes but recovery_retained < 0.20: loose radius
```

Primary pass criteria:

```text
exact M297/M270/old-key no-regression
M267/M264 first replay: 17 / 17 success drops
old-key compact replay: 0 accepted regressions
M183/M170 first replay: 17 / 17 success drops
recovery improvement retained vs M406 >= 0.20
```

Partial evidence criteria:

```text
all proof gates pass
0.10 <= recovery improvement retained vs M406 < 0.20
```

Partial evidence is not promotable. It should trigger a utility audit or a
second radius calibration, not a full public gate.

## Forbidden Shortcuts

- Do not change actor inputs or outputs.
- Do not make replay labels actor inputs.
- Do not lower exact, M267/M264, old-key, or M183/M170 proof thresholds.
- Do not run PPO until the no-PPO radius probe passes primary criteria.
- Do not promote a radius candidate without the full public gate.

## Decision

Admit:

```text
m419-active-set-radius-anchor-export-implementation
```

M419 should implement/export the radius-calibrated active-set v2 anchors and run
only no-update exact repair smokes. The actual projection probe should be M420.
