# M269 M268 Old-Surface Proof Washout Audit

M269 audits why M268 improved the M267 objective but failed old M183/M193 replay
proof surfaces. No PPO, actor update, promotion, or actor-input change was
performed.

## Question

M268 could have failed for several reasons:

- wrong-history sensitivity disappeared;
- normal-history behavior moved out of the safe near-boundary window;
- the M267-only corpus failed to cover older proof states;
- generic action anchors were too weak on fragile historical surfaces.

M269 asks which explanation is supported by the evidence and what repair should
be pre-registered next.

## Replay Failure Type

M268 did not lose wrong-history failure. It lost normal-history success on old
surfaces.

| Corpus | Rows | Candidate normal failures | Candidate success drops | Candidate wrong-history success | Gate |
| --- | ---: | ---: | ---: | ---: | --- |
| M183 M168 | 16 | 13 | 3 / 16 | 0.0 | false |
| M183 M170 | 17 | 14 | 3 / 17 | 0.0 | false |
| M193 M189 | 14 | 9 | 5 / 14 | 0.0 | false |
| M212 M204 | 17 | 0 | 17 / 17 | 0.0 | true |
| M223 M219 | 17 | 0 | 17 / 17 | 0.0 | true |
| M267 M264 | 17 | 0 | 17 / 17 | 0.0 | true |

The failed rows terminate by collision under normal history. That is
`proof_washout`, not a loss of wrong-history sensitivity.

## Action Drift

M268's first-action drift is larger on old failed surfaces than on retained
recent surfaces:

| Corpus | Gate | Mean first-action L2 drift | Max first-action L2 drift | Mean normal-margin delta |
| --- | --- | ---: | ---: | ---: |
| M183 M168 | false | 0.036561 | 0.050801 | -0.006228 |
| M183 M170 | false | 0.035605 | 0.049915 | -0.006575 |
| M193 M189 | false | 0.020956 | 0.032173 | -0.005204 |
| M212 M204 | true | 0.012793 | 0.018603 | -0.004233 |
| M223 M219 | true | 0.010537 | 0.013916 | -0.003670 |
| M267 M264 | true | 0.005967 | 0.007266 | -0.001991 |

The old surfaces are not simply failing because wrong-history margins improved
or because the target objective is unsteerable. They fail because normal-history
actions shift enough to move already-fragile rows into collision.

## Coverage

M267 coverage is not enough to protect older proof states.

| Corpus | Physical keys | Overlap with M267 keys | Target groups |
| --- | ---: | ---: | --- |
| M183 M168 | 14 | 9 | braking, lateral, yaw |
| M183 M170 | 15 | 10 | braking, lateral, yaw |
| M193 M189 | 11 | 11 | braking, yaw |
| M212 M204 | 13 | 13 | braking, yaw |
| M223 M219 | 13 | 13 | braking, yaw |
| M267 M264 | 13 | 13 | braking, yaw |

The M183 failures are partly outside M267 coverage: they include lateral target
rows and `9540` physical-pair keys not present in M267.

But M193 is more important diagnostically. M193 has full physical-key overlap
with M267 and still fails. Therefore the problem is not only missing physical
keys. The old hidden/action geometry is not protected by an M267-only snippet
objective plus generic action-anchor samples.

## Interpretation

M268 is a source-local objective overfit:

- M267 fixed sampled loss improves from `0.213681` to `0.212479`;
- M267 exact loss improves from `0.212996` to `0.211805`;
- M267 replay remains `17/17`;
- old M183/M193 replay surfaces fail before behavior or protected-key gates.

The old proof surfaces must be represented directly in the update objective or
anchor set. Generic action anchors are too coarse for these fragile boundary
states.

## Decision

Do not repeat M268 and do not run PPO.

The next repair should first build a source-balanced multi-surface anchor corpus
covering at least:

```text
M183 M168
M183 M170
M193 M189
M212 M204
M223 M219
M267 M264
old protected-key diagnostic 9944
```

The repair should validate source balance and loader compatibility before any
actor update. It should also consider trajectory anchors for the old M183/M193
rows because M268's first-action anchor was not enough to preserve closed-loop
normal success.

Decision:

```text
repair_with_multi_surface_anchor_corpus
```

Next step:

```text
m270-source-balanced-multi-surface-anchor-corpus
```
