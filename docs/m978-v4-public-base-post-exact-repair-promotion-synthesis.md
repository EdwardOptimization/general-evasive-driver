# M978 V4 Public Base Post Exact Repair Promotion Synthesis

## Purpose

M978 synthesizes the post-promotion guarded PPO readiness branch after M977
promoted the M974 exact-repaired checkpoint as the current public-gate base.

M978 does not train, run PPO, use private holdout, promote another checkpoint,
or make paper-level or real-vehicle claims.

## Evidence Summary

M972 tested the first guarded PPO smoke from alpha `1.0`.

Result:

```text
PPO completed
fresh/generalization gates passed
behavior gates passed
proof replay failed on M267/M264
M267/M264 success-drop count: 17 -> 15
failed rows: 6 and 15
```

This showed that the PPO proposal was behavior-retaining but not
proof-retaining.

M973 designed exact post-PPO repair/projection. The core rule was:

```text
PPO = proposal
exact M297/M270 full-corpus objectives = feasibility residuals
replay gates = nonlinear closed-loop acceptance
```

M974 tested repair candidates.

Result:

```text
raw-start repair exact pass: true
raw-start M267/M264 success-drop: 16 / 17
base-start exact pass: true
base-start M267/M264 first replay: 17 / 17
base-start M183/M170 first replay: 17 / 17
selected: runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

Direct line-search toward M972 raw had no exact-safe positive alpha under the
strict `1e-7` tolerance. Base-start repair was safer than raw-start repair.

M975 designed the full public gate for the selected candidate.

M976 ran that gate.

Result:

```text
six public replay surfaces pass: 6 / 6
source-diverse protected diagnostic: pass, 3 / 3
fresh public generalization: pass
moderate OOD: pass
behavior/ablation: pass
actor_inputs_changed: false
ppo_used: false
private_holdout_used: false
```

M977 promoted the selected exact-repaired checkpoint as the current public-gate
base:

```text
runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt
```

## Supported Claims

1. The M972 raw PPO proposal from alpha `1.0` was not acceptable as a raw
   checkpoint because it washed out wrong-history proof on M267/M264.

2. Exact full-corpus repair/projection is useful as a feasibility restoration
   layer after a PPO proposal. It produced a candidate that improves exact
   M297/M270 and passes first replay gates.

3. The selected M974 base-start exact repair is a valid public-gate base under
   the current public proof/generalization/behavior protocol.

4. Treating PPO as a proposal, not as an accepted update, remains the right
   workflow for this branch.

## Falsified Claims

1. A low-LR guarded 1024-step PPO proposal from alpha `1.0` can be accepted raw
   after broad behavior checks. It cannot; proof retention failed.

2. Direct interpolation toward the M972 raw PPO checkpoint is enough. It is not;
   the first positive line-search alpha already regressed exact objectives.

3. Raw-start exact repair is enough to fully recover the M972 proposal. It is
   not; row `15` remained wrong-history-safe.

4. First replay gates are enough for public-base promotion. They are not; M976
   full public gate was still required.

## Failure Taxonomy Summary

| Milestone | Failure type | Interpretation |
| --- | --- | --- |
| M972 | `proof_washout` | PPO preserved broad behavior but made wrong-history rows 6 and 15 safe |
| M974 raw-start | `objective_overfit` risk | Exact pass did not fully restore closed-loop M267/M264 proof |
| M976 | `none` | Full public gate passed |
| M977 | `none` | Public-gate promotion audit passed |

The dominant failure remains proof washout under PPO proposal movement, not
training instability or broad scenario regression.

## Public-Gate Overfit Risk

Risk level:

```text
moderate
```

Reasons:

- M974/M976 use established public replay surfaces and exact corpora that have
  been optimized repeatedly.
- The promoted candidate is a small exact-repair movement, not a broad new
  driving-capability jump.
- Private holdout remains unused.
- Fresh public and moderate OOD gates pass, but they are still public workflow
  gates rather than paper-level evidence.

Mitigations already present:

- six public replay surfaces;
- source-diverse protected diagnostic;
- fresh public and moderate-OOD evaluation;
- behavior ablation ordering;
- explicit old-key diagnostic reporting.

Needed before another PPO continuation:

```text
fresh current-base surface refresh
```

The system should not immediately start another PPO from the new base using
only the same M267/M297/M270 surfaces. That would risk becoming a public-row
gate-passing loop.

## Next Branch Decision

Decision:

```text
pivot_to_post_repair_surface_refresh
```

Open a new branch:

```text
v4_public_base_post_repair_surface_refresh
```

The next branch should refresh source-diverse proof/preference surfaces around
the new public-gate base before any further PPO continuation.

Next milestone:

```text
m979-v4-public-base-post-repair-surface-refresh-design
```

M979 should design a no-PPO surface refresh that asks:

```text
Are there fresh M974-family wrong-history boundary rows, preference rows,
and source-diverse protected rows that were not directly optimized by M972-M977?
```

Only after that refresh should another guarded PPO readiness branch be opened.
