# M383 Old-Key Local-Recovery Residual Implementation

M383 implements the training-only recovery residual designed in M382. This is
an infrastructure milestone only: no PPO was run, no checkpoint was promoted,
and the actor input/output contract was unchanged.

## What Changed

The exact repair path now accepts an optional old-key recovery corpus:

```text
--old-key-recovery-npz path/to/old_key_recovery_corpus.npz
```

The corpus contains:

```text
observation
preferred_hidden
rejected_hidden
recovery_action
rejected_anchor_action
weight
row_id
```

The deployable actor still receives only the existing P0 human-view observation
and recurrent hidden state, and still outputs direct steer / throttle / brake.
The recovery corpus is training-time metadata only.

## Loss

M383 adds:

```text
L_old_key_recovery =
  mean_i w_i || tanh(mean_pi(o_i, h_i^normal)) - a_i^recovery ||^2
  + lambda_wrong_anchor
    mean_i w_i || tanh(mean_pi(o_i, h_i^wrong)) - a_i^wrong_anchor ||^2
```

The wrong-history branch is anchored to its existing rejected action so the
normal branch can be nudged toward a recovery action without making the
wrong-history rollout safer by construction.

## Implementation

Files changed:

- `src/autodrift/intervention_objectives.py`
  - adds `OldKeyRecoverySnippets`;
  - adds `load_old_key_recovery_snippets`;
  - validates observation, hidden, action, weight, and row-id dimensions;
  - rejects non-finite values and actions outside `[-1, 1]`.
- `src/autodrift/exact_post_ppo_repair.py`
  - adds `exact_old_key_recovery_terms`;
  - logs recovery rows and preferred/wrong-anchor loss terms in exact summaries;
  - adds the recovery residual to exact repair when the corpus is provided;
  - exposes CLI knobs for `lambda_old_key_recovery` and
    `lambda_old_key_recovery_wrong_anchor`.
- `tests/test_exact_post_ppo_repair.py`
  - covers no-corpus zero terms;
  - covers loader validation and invalid action rejection;
  - covers finite differentiable recovery terms inside `repair_loss_terms`.

## No-Update Smoke

M383 exported a bootstrap recovery corpus from the M377 old-key preference
corpus:

```text
runs/m383_old_key_recovery_bootstrap_corpus/old_key_recovery_corpus.npz
```

The corpus uses the four current `gap_tail_row` entries. Its `recovery_action`
is the existing preferred action, not a simulator-searched recovery target.
This is deliberately only a loader/objective smoke corpus.

The no-update exact repair smoke was:

```text
runs/m383_old_key_recovery_no_update_smoke/summary.json
```

Key values:

```text
old_key_recovery_rows: 4
old_key_recovery_loss: 4.268774e-07
old_key_recovery_preferred_loss: 1.370522e-07
old_key_recovery_wrong_anchor_loss: 2.898252e-07
exact_lexicographic_pass: true
ppo_run: false
checkpoint_promoted: false
actor_inputs_changed: false
```

## Tests

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_exact_post_ppo_repair.py
```

Result:

```text
9 passed
```

## Decision

M383 completes the infrastructure needed to express an old-key local-action
recovery residual, but it does not yet prove recovery. The bootstrap corpus is
not a true local-search target corpus.

Next:

```text
m384-old-key-local-recovery-target-export
```

M384 should export replay-selected local recovery actions from the current
cumulative old-key gap-tail rows before any no-PPO repair proof probe.
