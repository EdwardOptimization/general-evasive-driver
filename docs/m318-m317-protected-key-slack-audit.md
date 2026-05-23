# M318 M317 Protected-Key Slack Audit

M318 audits the protected-key state after M317 promoted M316 alpha `0.0025`.
No PPO, actor update, promotion, or actor-input change was performed.

## Question

M318 asks whether protected key `9944|perturbed|28|28` is still a useful
single hard veto for the current M317 family.

The possible outcomes were:

- keep the single key if it has meaningful slack and remains representative;
- refresh a source-diverse protected surface if the key is a saturated
  singleton;
- redesign the protected-surface distribution gate if many current-family rows
  are also saturated;
- stop PPO if wrong-history sensitivity is disappearing.

## Current Base

Current public-gate base:

```text
runs/m316_m314_to_repaired_protected_key_bounded_interpolation/checkpoints/alpha_0_0025.pt
```

The M317 promotion is valid, but the accepted movement is tiny:

| Objective | Delta vs M314 |
| --- | ---: |
| Exact M297 rejected-history preference | -0.000000477 |
| Exact M270 source-balanced outcome | -0.000000298 |

## Protected-Key Slack

Protected key guard at M317:

| Policy | Pass | Normal margin | Wrong-history margin | Margin gap |
| --- | --- | ---: | ---: | ---: |
| m314_base | true | 0.199976 | 0.100100 | 0.099876 |
| m316_a0_0025 | true | 0.199995 | 0.100123 | 0.099873 |
| m239_a750 | false | 0.200336 | 0.099817 | 0.100519 |

The old protected-key normal-margin upper window is:

```text
max_normal_margin = 0.2
```

Remaining M317 slack:

```text
0.2 - 0.19999520261417003 = 0.00000479738582998
```

M316's alpha sweep shows the old key is the active trust-region constraint:

| Alpha | Protected pass | Normal margin |
| ---: | --- | ---: |
| 0.0000 | true | 0.199976 |
| 0.0025 | true | 0.199995 |
| 0.0050 | false | 0.200015 |
| 0.0100 | false | 0.200053 |
| 1.0000 | false | 0.207388 |

Exact M297/M270 allowed the entire direction through alpha `1.0`; the single
old protected key limited the accepted movement to `0.0025`.

## Comparison With M266/M267

M266 already answered a similar question for the M264 family. It found the old
key was a saturated diagnostic singleton, while a source-diverse current-family
surface still existed:

| M266 metric | Value |
| --- | ---: |
| Accepted wrong-history rows | 180 |
| Physical pairs | 13 |
| Left steps | 8 |
| Checkpoints | 3 |
| Targets | 2 |
| Mean normal margin | 0.005947 |
| Max normal margin | 0.010194 |
| Mean margin gap | 0.009323 |

M267 converted that surface into compact replay-aligned corpora:

| M267 current-base corpus metric | Value |
| --- | ---: |
| Rows | 17 |
| Physical pairs | 13 |
| Targets | 2 |
| Mean normal margin | 0.006068 |
| Max normal margin | 0.010193 |
| Mean margin gap | 0.009434 |

The M317 result has the same pattern:

- the old protected key remains discriminative;
- wrong-history success drops are retained on all six replay surfaces;
- the old key's normal-margin window, not exact M297/M270, is the immediate
  bottleneck;
- the old key now has only micro slack.

This is not evidence of wrong-history sensitivity loss. It is single-key window
saturation.

## Decision

Do not bypass `9944` silently, and do not run another PPO proposal yet.

Admit a source-diverse protected-surface refresh for the M317 family:

```text
m319-m317-family-protected-surface-refresh
```

The refresh should answer whether current-family source-diverse protected rows
exist away from the saturated old key. If they do, the next gate should become a
multi-key or distribution protected-surface gate. If the refreshed surface is
also saturated, the project needs a window-aware objective or terminal-margin
retention rule before more PPO.

Decision:

```text
admit_m319_m317_family_protected_surface_refresh
```
