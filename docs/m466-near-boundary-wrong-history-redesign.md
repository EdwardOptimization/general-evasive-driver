# M466 Near-Boundary Wrong-History Redesign

## Purpose

M466 converts the M465 high-slack negative result into a stricter proof path.
The goal is to prevent wrong-history proof from being satisfied by large-margin
rows where the policy changes slightly but still succeeds comfortably.

No training, PPO, checkpoint update, actor-input change, or checkpoint
promotion is performed.

## Evidence From M465

M465 targeted pair probing made one improvement over M462: wrong-history rows
entered the compact corpus. But the evidence is not proof-quality:

```text
wrong-history compact rows:             7
success-drop rows:                      0
collision-gap rows:                     0
obstacle-completion-drop rows:          0
positive-margin rows:                   7
label coverage:                         aes_feasible only
normal margin range:                    3.548402 to 7.612638
```

Additional near-boundary audit over the M465 wrong-history candidates:

```text
normal-success wrong-history rows with 0 < normal_margin <= 0.25:   8
accepted among those rows:                                           0
success-drop/collision/completion rows:                              0

normal-success wrong-history rows with 0 < normal_margin <= 0.50:  22
accepted among those rows:                                           0
success-drop/collision/completion rows:                              0

normal-success wrong-history rows with 0 < normal_margin <= 1.00:  47
accepted among those rows:                                           0
success-drop/collision/completion rows:                              0
```

So near-boundary rows exist, but wrong-history currently does not cause
meaningful closed-loop degradation there. The rows with positive wrong-history
margin gap only appear once the normal branch has several meters of slack.

## Diagnosis

### 1. Current wrong-history selection optimizes response ambiguity, not risk

M464 improved source diversity by selecting pairs with stronger hidden/current
separation and matched-current geometry. That helps create wrong-history action
differences, but it does not guarantee the left-side continuation is near a
failure boundary.

### 2. High-slack margin deltas are diagnostic only

A `0.02 m` to `0.06 m` margin drop on a `3 m` to `7 m` normal margin is real
but not outcome-critical. It can show mild sensitivity, not reliance on
history for emergency success.

### 3. Near-boundary rows show almost no wrong-history effect

The low normal-margin rows in M465 are mostly `drift_required` or
`unavoidable`, but wrong-history action distance and continuation divergence
are too small to trigger margin, completion, collision, or success gaps.

### 4. The next proof surface must be normal-margin-aware

The selector needs to classify rows into at least three categories:

```text
proof_candidate:
  normal succeeds, normal margin is low, wrong history causes success/collision/
  completion drop or meaningful margin drop.

near_boundary_no_effect:
  normal succeeds with low margin, but wrong history does not degrade outcome.

high_slack_diagnostic:
  wrong history changes action or margin, but normal margin is too high for a
  proof claim.
```

## Redesign

### Near-Boundary Wrong-History Selector

M467 should implement a small selector/auditor over existing selector candidate
rows. It should not run new policy rollouts; it should make the proof criteria
explicit and reusable.

Inputs:

```text
runs/m465_targeted_wrong_history_selector/candidates.csv
```

Core filters:

```text
variant == wrong_matched_history
matched_current_pass == true
normal_success == true
0 < normal_margin <= normal_margin_ceiling
```

Default proof ceiling:

```text
normal_margin_ceiling = 0.75 m
```

Why `0.75`: it includes the M465 low-margin rows up to the practical boundary
region, but excludes the `3.5 m` to `7.6 m` high-slack rows that created false
comfort.

Proof outcome conditions:

```text
success_drop
collision_gap
obstacle_completion_drop with return_gap >= 1.0
margin_gap >= 0.02 under the normal-margin ceiling
```

The selector should write:

```text
near_boundary_candidates.csv
proof_candidates.csv
near_boundary_no_effect.csv
high_slack_diagnostics.csv
summary.json
```

### Pass Criteria For Wrong-History Gate Expansion

Wrong-history proof expansion requires:

```text
proof_candidates >= 16
probe_seed_count >= 3
obstacle_label_count >= 2
target_count >= 2
success_or_collision_or_completion_rows >= 4
single_seed_share <= 0.50
single_label_share <= 0.60
```

Rows above `normal_margin_ceiling` can remain diagnostic but cannot count
toward proof.

### Expected Outcome On M465

M465 is expected to fail this stricter selector because its wrong-history
effect is high-slack margin-only. That failure is useful: it will make the next
blocker precise. If M467 fails, the project should stop reusing M457/M464
without changing the task family and instead design a harder near-boundary
wrong-history task.

## Decision

```text
admit_m467_near_boundary_wrong_history_selector
```

Do not expand wrong-history proof gates from M465. First implement the
normal-margin-aware selector and classify the current evidence.
