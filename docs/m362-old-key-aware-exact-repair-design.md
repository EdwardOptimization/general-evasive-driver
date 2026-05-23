# M362 Old-Key-Aware Exact Repair Design

M362 designs the next repair/projection step after M361. It does not run PPO,
actor updates, replay, or promotion.

## Problem

The current exact post-PPO repair optimizes two differentiable full-corpus
objectives:

```text
M297 rejected-history preference
M270 source-balanced outcome intervention
```

M356 proved that this repair can select a checkpoint that is lexicographically
feasible on M297/M270. M357 then showed the same checkpoint still fails
source-diverse old-key neighborhood proof and M267/M264 first replay. M358 had
to clip the direction to `alpha=0.00025`; `alpha=0.0005` already fails old-key
neighborhood replay.

So the missing piece is not another scalar PPO auxiliary coefficient. The repair
objective itself is blind to the old-key neighborhood proof surface.

## Design Goal

Make old-key neighborhood proof visible to exact repair before the expensive
closed-loop replay gate.

The repaired candidate should be selected under this lexicographic order:

1. exact M297 no-regression versus base;
2. exact M270 no-regression versus base;
3. old-key differentiable surrogate no-regression versus base;
4. small action drift on old-key preferred/source histories;
5. small trainable-parameter distance to base;
6. optional distance toward the raw PPO proposal.

Closed-loop old-key targeted replay remains the authoritative proof gate. The
new surrogate is a repair residual, not a replacement for replay.

## Old-Key Surrogate Corpus

Create an `old_key_preference_corpus.npz` from the M341 compact old-key
neighborhood rows.

For each compact row:

```text
source snapshot = source condition at source_step
paired snapshot = paired condition at paired_step
relocated observation = source snapshot with compact obstacle relocation
preferred hidden = source/current-history hidden
rejected hidden = paired/wrong-history hidden
preferred action = base policy deterministic action on preferred hidden
rejected action = base policy deterministic action on rejected hidden
```

Required arrays:

```text
observation
preferred_hidden
rejected_hidden
preferred_action
rejected_action
weight
row_id
seed_block
source_step
target_bucket
reference_normal_margin
reference_wrong_history_margin
reference_margin_gap
```

This is the same student-input contract used by M297/M270 style corpora:
deployable observation plus recurrent hidden states. It does not add `mu`, slip,
TTC, path errors, labels, or oracle feasibility to the actor.

## Loss Terms

Add optional old-key terms to `exact_post_ppo_repair`:

```text
L_old_key_preferred_anchor =
  weighted || mean_pi(o, h_preferred) - a_preferred_base ||^2

L_old_key_source_preference =
  softplus(logp_pi(a_preferred_base | o, h_rejected)
           - logp_pi(a_preferred_base | o, h_preferred)
           + margin_source)

L_old_key_wrong_preference =
  softplus(logp_pi(a_preferred_base | o, h_rejected)
           - logp_pi(a_rejected_base | o, h_rejected)
           + margin_wrong)
```

The first term protects normal/source branch actions on accepted rows. The
second keeps correct-history likelihood above wrong-history likelihood for the
same preferred action. The third keeps wrong-history behavior from collapsing
into the normal safe action, matching the M279-M296 lesson that repairing only
the normal branch can erase self-ID proof.

The old-key exact metric should be the weighted sum:

```text
old_key_surrogate =
  old_key_source_preference
+ lambda_wrong * old_key_wrong_preference
+ lambda_anchor * old_key_preferred_anchor
```

Repair feasibility should require:

```text
old_key_surrogate(candidate)
  <= old_key_surrogate(base) + tolerance
```

## Row Weighting

Weights should emphasize rows most relevant to the M357/M358 failure:

- rows that fail in the M356 direct best-step candidate;
- rows near the old-key accepted-window boundary;
- rows whose accepted status flips by `alpha=0.0005`;
- rows with small baseline normal-margin slack;
- rows with large wrong-history sensitivity.

The first implementation can use a deterministic clipped weight:

```text
weight =
  1
+ 4 * direct_candidate_regression
+ 2 * alpha_0005_regression
+ clip(abs(reference_margin_gap), 0, 0.05) / 0.05
```

This is training-time metadata only. None of these flags enter the deployable
actor.

## Repair Selection

Extend the exact repair selection row with:

```text
old_key_surrogate_loss
old_key_surrogate_delta_vs_base
old_key_surrogate_no_regression
old_key_anchor_loss
old_key_source_preference_loss
old_key_wrong_preference_loss
```

Selection should prefer:

```text
1. exact M297/M270 and old_key_surrogate all feasible
2. smallest positive violation across M297/M270/old_key
3. lowest total repair loss
4. lowest old-key preferred-anchor drift
5. lowest trainable-parameter distance to base
6. earlier step
```

This prevents another M355-style final-step artifact and prevents an exact-only
best step that immediately needs micro-alpha clipping.

## Acceptance Stack

After implementation, a candidate from old-key-aware exact repair must still
pass the existing gates in this order:

1. exact M297/M270 no-regression;
2. old-key surrogate no-regression;
3. old-key neighborhood targeted replay and replay-gate adapter;
4. source-diverse protected gates;
5. M183/M170 and M267/M264 first replay gates;
6. full public gate only in a separate milestone.

If the old-key-aware repair still only accepts `alpha <= 0.00025`, classify the
result as objective-overfit or proof-washout and redesign the old-key corpus,
instead of chaining longer PPO.

## M363 Implementation Plan

Implement without PPO:

```text
src/autodrift/old_key_preference_corpus.py
```

Responsibilities:

- export old-key compact rows to NPZ + metadata CSV;
- reuse M341 targeted snapshot collection where possible;
- store preferred/rejected hidden states and base deterministic actions;
- validate shape, finite values, group diversity, and actor-input contract.

Extend:

```text
src/autodrift/exact_post_ppo_repair.py
```

Add optional CLI arguments:

```text
--old-key-preference-npz
--lambda-old-key
--lambda-old-key-anchor
--old-key-tolerance
--old-key-source-margin
--old-key-wrong-margin
```

If no old-key corpus is provided, existing behavior must remain unchanged.

Focused tests:

```text
tests/test_old_key_preference_corpus.py
tests/test_exact_post_ppo_repair.py
```

M363 should end with implementation tests and a small deterministic synthetic
repair test. It should not run PPO.

## Decision

Admit:

```text
m363-old-key-aware-repair-implementation
```

Decision:

```text
admit_m363_old_key_aware_repair_implementation
```
