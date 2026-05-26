# M1031 V4 Public Base Candidate B Temporal-Safe Projection Probe

## Purpose

M1031 implements and runs the no-PPO temporal-safe interpolation/projection
probe designed in M1030.

The question is:

```text
Does any bounded fraction of an M1029 exact-repair direction keep M997 temporal
exact retention, keep M297/M270 exact no-regression, and then pass first replay?
```

M1031 does not run PPO, promote a checkpoint, use private holdout, relax M997
thresholds, or change actor inputs.

## Implementation

New tooling:

```text
src/autodrift/candidate_b_temporal_safe_projection_probe.py
tests/test_candidate_b_temporal_safe_projection_probe.py
```

The runner saves a checkpoint for every evaluated projection and writes:

```text
runs/m1031_candidate_b_temporal_safe_projection_probe/projection_metrics.csv
runs/m1031_candidate_b_temporal_safe_projection_probe/candidate_checkpoints.csv
runs/m1031_candidate_b_temporal_safe_projection_probe/first_replay_summary.csv
runs/m1031_candidate_b_temporal_safe_projection_probe/route_decision.csv
runs/m1031_candidate_b_temporal_safe_projection_probe/summary.json
```

Important implementation correction:

```text
The first replay loop scans all eligible projection candidates, not only the
largest alpha candidate. This is necessary because M1031 asks whether any
temporal/exact-safe fraction exists.
```

## Inputs

Base checkpoint:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

Repair directions:

```text
raw_conflict_s40:
  runs/m1029_candidate_b_post_ppo_exact_repair_raw_s40_seed61028/candidate_checkpoint.pt

base_conflict_s40:
  runs/m1029_candidate_b_post_ppo_exact_repair_base_s40_seed61029/candidate_checkpoint.pt

line_conflict_s40:
  runs/m1029_candidate_b_post_ppo_exact_repair_line_s40_seed61030/candidate_checkpoint.pt
```

Alpha grid:

```text
0.05,0.10,0.15,0.20,0.25,0.30,0.35,0.40,0.45,0.50,0.60,0.75,1.00
```

Exact corpora:

```text
M997 temporal:
  runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz

M297 rejected-history preference:
  runs/m297_current_family_rejected_preference_objective/rejected_history_preference_corpus.npz

M270 outcome intervention:
  runs/m270_source_balanced_multi_surface_anchor/outcome_intervention_snippets.npz
```

First replay surfaces:

```text
M267/M264
M183/M170
```

## Exact Projection Results

M1031 evaluates `39` projected checkpoints.

```text
actor_input_change_count: 0
temporal_exact_pass_count: 16
temporal_and_exact_pass_count: 16
eligible_candidate_count: 14
```

All temporal-safe candidates also pass M297/M270 exact no-regression. The M1029
repair directions are therefore not blocked at the exact-objective layer after
projection.

Highest eligible raw-start projection:

| Source | Alpha | M997 exact | Action L2 mean | M297 delta | M270 delta |
| --- | ---: | --- | ---: | ---: | ---: |
| raw_conflict_s40 | 0.30 | true | 0.013229 | -0.000184 | -0.000010 |

Highest eligible base/line projections:

| Source | Alpha | M997 exact | Action L2 mean | M297 delta | M270 delta |
| --- | ---: | --- | ---: | ---: | ---: |
| base_conflict_s40 | 0.25 | true | 0.008270 | -0.000089 | -0.000005 |
| line_conflict_s40 | 0.25 | true | 0.008270 | -0.000089 | -0.000005 |

The M997 action-drift gate is the active upper bound:

```text
raw_conflict_s40 alpha 0.30 passes action L2 mean 0.013229 <= 0.015
raw_conflict_s40 alpha 0.35 fails action L2 mean 0.015373 > 0.015
base/line alpha 0.25 pass action L2 mean 0.008270
base/line alpha 0.30 fail temporal exact despite action L2 mean 0.009847
```

## First Replay Results

M1031 then scans all `14` eligible candidates in ranked order.

Result:

```text
first_replay_pass_candidate_found: false
```

M267/M264:

```text
Several projected candidates pass M267/M264 at 17/17 success drops with row15
retained.
```

Examples:

| Candidate | M267/M264 success drops | Row15 retained |
| --- | ---: | --- |
| base_conflict_s40 alpha 0.25 | 17/17 | true |
| line_conflict_s40 alpha 0.25 | 17/17 | true |
| raw_conflict_s40 alpha 0.15 | 17/17 | true |
| raw_conflict_s40 alpha 0.10 | 17/17 | true |
| raw_conflict_s40 alpha 0.05 | 17/17 | true |

M183/M170:

```text
No eligible candidate passes M183/M170.
```

Most M1031 candidates fail M183/M170 because the normal branch becomes unsafe on
many rows. The smallest raw-start projection is much closer:

```text
raw_conflict_s40 alpha 0.05:
  M183/M170 success drops: 16/17
  failed row: row_id 16
  normal_success: false
  wrong_history_success: false
  normal_margin: -0.000165
  wrong_history_margin: -0.006597
```

This is not wrong-history sensitivity disappearing. It is a normal-branch
terminal-margin cliff on M183/M170 row16.

## Interpretation

M1031 is a useful negative result with a sharper diagnosis than M1029:

```text
M1029 endpoint repair candidates were too large for M997 temporal retention.
M1031 projection can recover temporal exact retention and M297/M270 exact
no-regression.
M1031 projection can also recover M267/M264 row15 for some candidates.
But the same projected directions still break M183/M170, usually through
normal-branch terminal-margin loss.
```

The closest miss is `raw_conflict_s40 alpha 0.05`, which keeps M267/M264 and
misses M183/M170 only on row16 by `-0.000165` normal margin. This suggests the
next objective/gate gap is not only M997 temporal action drift and not only
M267 row15 wrong-history retention. M183/M170 row16 normal terminal-margin
retention must become first-class before any full public gate route.

## Decision

```text
candidate_b_temporal_safe_projection_proof_washout
```

Failure type:

```text
proof_washout
```

Next milestone:

```text
m1032-v4-public-base-candidate-b-temporal-projection-first-replay-failure-audit
```

M1032 should audit the M183/M170 row16 normal-margin cliff and decide whether
the next implementation should be:

```text
1. a finer low-alpha projection scan around raw_conflict_s40 alpha < 0.05;
2. a direct exact repair objective that includes M997 temporal retention and
   M183/M170 row16 terminal-margin/action retention;
3. or a replay-calibrated active-set projection with M183 row16 in the hard
   constraint set.
```

Do not run longer PPO or promote from M1031.
