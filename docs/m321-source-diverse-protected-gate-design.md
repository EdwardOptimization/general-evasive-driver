# M321 Source-Diverse Protected Gate Design

M321 designs how the M320 compact protected-surface corpora should become
first-class acceptance gates before any more PPO. No PPO, actor update,
promotion, or actor-input change was performed.

## Problem

The old protected key `9944|perturbed|28|28` remains discriminative, but M317
left it nearly saturated:

```text
normal margin = 0.19999520261417003
max_normal_margin = 0.2
slack ~= 4.8e-6
```

If this single key remains the only hard protected-surface veto, future PPO
proposal movement will be dominated by one saturated row. M319 and M320 show
that source-diverse protected rows still exist away from that saturated window:

```text
M319: 180 accepted wrong-history rows across 13 physical pairs, 8 left steps,
      3 checkpoints, and 2 targets.

M320: compact 17-row / 13-physical-pair corpora for m316_a0_0025, m314_base,
      and m316_repaired; all objective and replay sanity gates pass.
```

## Design Decision

M321 does not delete `9944`. It changes the role:

```text
9944:
  diagnostic singleton and historical continuity check

M320 corpora:
  source-diverse protected-surface gate for future candidate acceptance
```

This means a future candidate should not be accepted because it only passes
aggregate return or exact M297/M270. It must also retain the refreshed
source-diverse protected surface.

## Protected Gate Bundle

The protected gate bundle should include three compact corpora:

| Corpus | Purpose |
| --- | --- |
| `m316_a0_0025` corpus | current-base protected surface |
| `m314_base` corpus | previous-base continuity surface |
| `m316_repaired` corpus | repaired PPO endpoint surface |

Required artifacts:

```text
runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv
```

Each corpus must be evaluated with closed-loop replay:

```text
normal-history success must not regress;
wrong-history success drops must be retained;
normal margin regression must stay within tolerance;
margin gap regression must stay within tolerance.
```

## Acceptance Order

For the next PPO proposal or repaired actor candidate:

```text
1. Exact M297 rejected-history preference no-regression.
2. Exact M270 source-balanced outcome no-regression.
3. M320 source-diverse protected replay bundle.
4. 9944 protected-key diagnostic report.
5. First replay gates if not already included.
6. Full replay stack.
7. Behavior seeds 9505/9506.
8. Promotion decision.
```

If a candidate passes the M320 protected bundle but fails `9944` only by the
old normal-margin window, it is not automatically promotable. It should be
classified as:

```text
single_key_window_saturation
```

and moved to a dedicated audit milestone before promotion. That audit can decide
whether the source-diverse protected gate is sufficient evidence to override
the old single-key window for that candidate.

## Implementation Need

M321 admits an implementation milestone to make the protected bundle runnable
and reviewable as one gate, instead of manually running several replay commands.

The implementation should:

- load a small JSON spec listing baseline/candidate policies and corpora;
- run the relevant `boundary_outcome_replay_gate` checks;
- run or ingest the `9944` diagnostic;
- emit a single summary with gate tiers and failure taxonomy;
- never change actor inputs.

The first use should be diagnostic, not promotion: run the new bundle against
known candidates such as M314, M316 alpha `0.0025`, and repaired endpoints to
confirm it matches the documented M320 replay sanity.

## Decision

Admit:

```text
m322-source-diverse-protected-gate-implementation
```

Decision:

```text
admit_m322_source_diverse_protected_gate_implementation
```
