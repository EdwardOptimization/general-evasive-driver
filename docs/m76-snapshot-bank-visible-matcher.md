# M76 Snapshot-Bank Visible Matcher

M75 preserved active-probe history with snapshot-level obstacle relocation, but
it still paired nominal and perturbed rollouts by a shared target obstacle
distance. The useful outcome-sensitive rows failed strict visible matching,
while strict visible rows had weak outcome differences.

M76 changes the pairing stage:

```text
collect many active-probe snapshots per condition
pair nominal and perturbed snapshots by visible response/context distance
then apply M75 obstacle relocation and wrong-history replay
```

## Code Changes

Added:

```text
src/autodrift/snapshot_bank_relocation.py
tests/test_snapshot_bank_relocation.py
```

The new harness:

- collects active-probe `DecisionSnapshot` banks over an obstacle-distance
  window;
- ranks nominal/perturbed snapshot pairs by visible response plus context
  distance;
- optionally filters pre-relocation visible distances;
- applies M75 snapshot obstacle relocation to each selected pair;
- reuses the existing normal / wrong-history replay and outcome-sensitive
  summary logic.

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q \
  tests/test_snapshot_bank_relocation.py tests/test_outcome_sensitive_corpus.py
```

Result:

```text
13 passed
```

Final validation:

```text
git diff --check
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
209 passed
```

## Strict Smoke

Command:

```text
conda run -n autodrift python -m autodrift.snapshot_bank_relocation \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m74_active_probe_near_miss_seeds.csv \
  --seed 8400 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 16 \
  --bank-obstacle-distance-range 5,12 \
  --bank-stride-steps 2 \
  --bank-max-snapshots 80 \
  --bank-max-pairs-per-seed 8 \
  --snapshot-relocation-distances 11,12 \
  --snapshot-relocation-lateral-offsets=-1,0,1 \
  --snapshot-relocation-half-widths 0.8,1.0,1.2 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.35 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.25 \
  --probe-brake-level 0.20 \
  --probe-period-steps 20 \
  --top-k 40 \
  --run-dir runs/m76_snapshot_bank_relocation_strict_seed8400
```

Result:

| Run | Candidates | Strict Visible | Margin-Gap Rows | Accepted | Max Gap | Mean Visible Distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bank strict | 432 | 144 | 2 | 0 | 0.011437 | 0.234060 |

Compared with M75, visible-state matching improved substantially:

```text
M75 visible distance mean: about 0.49 - 0.55
M76 visible distance mean: 0.234060
```

But the stronger matching also selected less outcome-sensitive states. Strict
accepted snippets remain zero.

## Relaxed Diagnostic

M76 then ran a deliberately relaxed diagnostic:

```text
--max-context-distance 0.06
--max-normal-margin 0.60
--run-dir runs/m76_snapshot_bank_relocation_relaxed_seed8401
```

Result:

| Run | Candidates | Visible Matches | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: |
| bank relaxed | 432 | 162 | 1 | 0.011437 |

Accepted relaxed row:

| Seed | Pair Rank | Nominal Step | Perturbed Step | Response Dist | Context Dist | Body X | Body Y | Half Width | Perturbed Normal Margin | Perturbed Wrong Margin | Gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8108 | 6 | 30 | 34 | 0.268191 | 0.052291 | 12.0 | -1.0 | 0.8 | 0.548486 | 0.537049 | 0.011437 |

This is not strict evidence:

- context distance is just above the strict `0.05` threshold;
- the normal margin is far above the strict near-boundary cap `0.20`.

It does show that the bank matcher can recover a visible-near, history-sensitive
row that M75's same-target pairing did not promote.

## Conclusion

M76 is an infrastructure pass and a negative strict gate result.

What improved:

- visible-state matching is much better than M75;
- the harness can find a relaxed wrong-history margin-loss row;
- selected pairs expose exactly which constraint blocks promotion.

What still fails:

- strict context threshold blocks the best relaxed row by a small amount;
- strict near-boundary normal-margin cap blocks the same row by a large amount;
- current relocation grid is coarse and not boundary-seeking.

## Next Step

M77 should make relocation boundary-aware:

```text
for each visible-matched snapshot-bank pair
adaptively sweep or search obstacle body position / half-width
target normal margin in [0.0, 0.20]
then measure wrong-history margin loss
```

This directly attacks the M76 blocker: the bank matcher can find matched states,
but the relocation grid needs to place the obstacle on the decision boundary
instead of using a coarse preset grid.
