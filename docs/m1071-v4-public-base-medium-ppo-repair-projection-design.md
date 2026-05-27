# M1071 V4 Public Base Medium PPO Repair Projection Design

## Purpose

M1071 designs the repair/projection path after M1069 failed as proof-washout.
It does not run PPO, train actor weights, promote, or use private holdout.

## Inputs

```text
base_checkpoint: runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
proposal_checkpoint: runs/ppo_m1069_expanded_gate_medium_seed61069/checkpoint.pt
failure_audit: docs/m1070-v4-public-base-medium-ppo-proof-washout-audit.md
proposal_summary: runs/m1069_expanded_gate_medium_ppo_seed61069/summary.json
```

The M1069 proposal is useful only as a proposal direction. It is not a base:

```text
exact_pass: false
public_replay_pass: false
family_intersection_pass: false
source_diverse_pass: false
generalization_pass: true
behavior_pass: true
```

## Design Premise

M1070 localized the failure:

```text
M297/M270 exact losses: no regression
combined active-set exact contract: failed
old public replay: 3 / 6 surfaces failed
M1061 family-intersection: 0 / 3 source gates passed
source-diverse continuity: 1 / 3 source gates passed
failure mechanism: wrong-history branches became marginally safe
```

Therefore the next step cannot be another PPO repeat. It must first build a
projection surface that treats proof retention as a feasibility problem.

## Why Existing Projection Is Not Enough

The existing combined active-set repair/projection tooling is useful, but the
M1069 failure is wider than the old Candidate-B active set:

```text
existing M1037 anchor:
  M183 row16 + M267 row15 focused active-set anchor

M1069 failed rows:
  old M183/M168 rows 9,10
  old M183/M170 row 10
  old M267/M264 row 15
  M1061 short61049 rows 16,22,23,24
  M1061 short61050 rows 16,17,23,24,25,26
  M1061 short61051 rows 16,17,23,24,25,26
  source-diverse M317/M314 row 15
```

A repair that only protects old row15/row16 can still pass the old exact
contract while washing out the refreshed family-intersection surface. M1069
proved this risk directly.

## Required Projection Corpus

M1072 should export a combined failed-row projection corpus before any repair
optimizer runs.

The corpus must include:

```text
1. old public failed rows
   m183_m168: rows 9,10
   m183_m170: row 10
   m267_m264: row 15

2. family-intersection failed rows
   short61049: rows 16,22,23,24
   short61050: rows 16,17,23,24,25,26
   short61051: rows 16,17,23,24,25,26

3. source-diverse failed rows
   m317_continuity_surface: row 15
   m314_continuity_surface: row 15
```

It should preserve source identity:

```text
surface
source_policy
source_checkpoint
boundary_corpus_npz
boundary_corpus_csv
row_id
physical_pair_key
wrong_history_margin_after_m1069
normal_margin_after_m1069
```

The projection should not collapse these into one unlabeled row set. The same
row id can mean different source-policy constraints.

## Export Method

Use the existing boundary corpus NPZ/CSV artifacts where available:

```text
runs/m1061_short61049_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz
runs/m1061_short61050_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz
runs/m1061_short61051_boundary_outcome_corpus_seed10570/boundary_outcome_corpus.npz
```

For old public and source-diverse surfaces, use their existing replay corpus
NPZ/CSV if present; otherwise M1072 should first export or reconstruct the
boundary snapshot corpus from the replay source before attempting repair.

For rejected-history action targets, use source-policy-specific anchors:

```text
short61049 rows -> source checkpoint runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
short61050 rows -> source checkpoint runs/ppo_m1050_guarded_short_repeat_seed61050/checkpoint.pt
short61051 rows -> source checkpoint runs/ppo_m1050_guarded_short_repeat_seed61051/checkpoint.pt
old/source-diverse rows -> M1049 public-gate base checkpoint
```

This keeps the family-intersection gate honest: the repair should preserve
source-diverse wrong-history behavior rather than overfitting one checkpoint's
action targets.

## Projection Probe Order

After the corpus export exists, the repair/projection probe should run in this
order.

### Stage A: interpolation boundary

Interpolate from M1049 base toward M1069 raw:

```text
alpha: 0.0, 0.001, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0
```

Acceptance:

```text
exact full contract pass
old public replay pass
M1061 family-intersection pass
source-diverse pass
fresh/OOD pass
behavior pass
```

If a nonzero alpha passes, it is only a repaired/projection candidate, not a
promotion candidate. It must route to a full public-gate design or repeat.

### Stage B: exact repair from raw/base

If interpolation cannot keep useful alpha, run exact repair candidates:

```text
start_mode:
  repair_from_raw
  repair_from_base
  line_search_boundary

train_scope:
  actor_coupling only

losses:
  M297 rejected-history preference
  M270 outcome intervention
  combined active-set action anchor
  M1072 failed-row family/source conflict loss
  trust region to M1049 base
  optional weak distance-to-M1069 raw
```

Acceptance order stays lexicographic:

```text
1. actor input contract unchanged
2. exact full contract pass
3. old public replay pass
4. M1061 family-intersection pass
5. source-diverse pass
6. fresh/OOD pass
7. behavior pass
8. no promotion/private holdout
```

Do not accept a candidate because the optimizer loss improves if any replay
proof gate fails.

## Hard Rollback Rules

Reject any projection candidate if:

```text
actor_inputs_changed == true
exact_pass == false
public_replay_pass == false
family_intersection_pass == false
source_diverse_pass == false
generalization_pass == false
behavior_pass == false
promoted == true
private_holdout_used == true
```

Specific row guards:

```text
M267/M264 row15 wrong_history_success must be false.
M183/M168 rows 9,10 wrong_history_success must be false.
M183/M170 row10 wrong_history_success must be false.
M1061 short61049 rows 16,22,23,24 wrong_history_success must be false.
M1061 short61050 rows 16,17,23,24,25,26 wrong_history_success must be false.
M1061 short61051 rows 16,17,23,24,25,26 wrong_history_success must be false.
M317/M314 row15 wrong_history_success must be false.
```

## Next Milestone

M1072 should not run PPO or optimize actor weights. It should export and
validate the M1069 failed-row projection corpus:

```text
m1072-v4-public-base-medium-ppo-failed-row-projection-corpus-export
```

If M1072 cannot build a source-diverse combined corpus, route to corpus-tooling
implementation before any projection optimizer.

## Decision

```text
medium_ppo_repair_projection_design_route_to_failed_row_corpus_export
```
