# M1029 V4 Public Base Candidate B Post-PPO Exact Repair Probe

## Purpose

M1029 runs the no-PPO exact post-PPO repair/projection probe designed in M1028.

It tests whether the M1026 raw PPO proposal can be repaired with exact M297/M270
objectives, M293 replay trajectory anchor, and M393 current-family row15
conflict residual before any first replay or full public gate.

M1029 does not run PPO, promote, use private holdout, or change actor inputs.

## Inputs

Base checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Raw PPO proposal:

```text
runs/ppo_m1026_candidate_b_guarded_smoke_seed61026/checkpoint.pt
```

Exact repair corpora:

```text
runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz
runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
runs/m293_current_family_rejected_history_ppo_repair_design/m267_failed_rows_extra4_anchor.npz
runs/m393_current_family_rejected_boundary_targets/current_family_conflict_corpus.npz
```

Temporal exact corpus:

```text
runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz
```

## Candidate Generation

Three candidates were generated with `python -m autodrift.exact_post_ppo_repair`.

| Candidate | Start mode | Checkpoint | M297 delta | M270 delta | Exact M297/M270 pass |
| --- | --- | --- | ---: | ---: | --- |
| raw_conflict_s40 | `repair_from_raw` | `runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/candidate_checkpoint.pt` | -0.000571609 | -0.000009418 | true |
| base_conflict_s40 | `repair_from_base` | `runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/candidate_checkpoint.pt` | -0.000331402 | -0.000004232 | true |
| line_conflict_s40 | `line_search_boundary` | `runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/candidate_checkpoint.pt` | -0.000331402 | -0.000004232 | true |

The M393 current-family conflict residual is finite in all candidates:

```text
raw_conflict_s40 current_family_conflict_loss: 0.007068202830851078
base_conflict_s40 current_family_conflict_loss: 0.008854920044541359
line_conflict_s40 current_family_conflict_loss: 0.008854920044541359
```

So the repair tool can optimize M297/M270 while reading the row15 conflict
corpus. The blocker is not M297/M270 feasibility.

## Temporal Exact Gate

M1029 then evaluated all three candidates with the M997 temporal exact
retention gate before first replay.

Result:

```text
exact_gate_pass_count: 0 / 3
selected_candidate: none
```

| Candidate | Weighted total | Action L2 mean | Action L2 max | Total pass | Normal NLL pass | Action mean pass | Exact gate |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| raw_conflict_s40 | -0.874429814 | 0.043320605 | 0.055655476 | false | false | false | false |
| base_conflict_s40 | -0.876566964 | 0.032059840 | 0.040694769 | false | false | false | false |
| line_conflict_s40 | -0.876566964 | 0.032059840 | 0.040694769 | false | false | false | false |

The key failing threshold is:

```text
candidate_action_l2_mean <= 0.015
```

Observed:

```text
raw_conflict_s40: 0.043320605
base_conflict_s40: 0.032059840
line_conflict_s40: 0.032059840
```

The candidates also fail the temporal weighted-total and normal-NLL retention
checks, but the action-drift failure alone is sufficient to block them.

## Gate Decision

Per M1028 gate order, candidates that fail M997 temporal exact retention must
not enter first replay.

Therefore M1029 intentionally does not run:

```text
M267/M264 first replay
M183/M170 first replay
full public gate
promotion/generalization gate
private holdout
```

## Interpretation

M1029 is a useful negative result:

```text
M297/M270 exact repair with M393 row15 conflict is feasible.
M997 temporal retention is not preserved by the existing repair objective.
```

This means the repair problem has two active proof families:

```text
1. current-family wrong-history branch retention:
   M267/M264 row15 must remain wrong-history failing.

2. temporal sequence retention:
   M997 normal action/logp behavior must remain within the exact temporal gate.
```

The current `exact_post_ppo_repair` objective handles the first family through
M297/M270/M293/M393, but it does not include M997 temporal action/logp
retention as an optimization term. The M1029 candidates drift too far before
they can be replay-gated.

## Route Decision

Do not run longer PPO.

Do not run first replay for these candidates.

Do not relax the M997 temporal exact gate.

The next milestone should design temporal-retention-aware exact repair:

```text
add M997 temporal normal-sequence action/logp retention into the repair
objective or add a temporal-safe interpolation/projection layer before first
replay.
```

The design should decide between:

```text
Option A:
  integrate M997 temporal action/logp losses into exact_post_ppo_repair

Option B:
  run exact repair as a proposal, then line-search/interpolate back to the
  nearest M997-temporal-safe point

Option C:
  constrain train_scope further, e.g. actor_mean-only or lower-rank correction,
  if actor_coupling changes are the source of temporal action drift
```

## Decision

```text
candidate_b_post_ppo_exact_repair_temporal_regression_route_to_temporal_retention_design
```

Next milestone:

```text
m1030-v4-public-base-candidate-b-temporal-retention-repair-design
```
