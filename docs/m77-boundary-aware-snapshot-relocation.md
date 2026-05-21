# M77 Boundary-Aware Snapshot Relocation

M76 improved visible-state matching, but its coarse relocation grid mostly
produced either high-margin safe rows or collision-to-collision rows. M77 tests
whether a denser obstacle-width sweep around the M76 high-signal region can
place matched snapshots on the clearance boundary.

This is a gate experiment using the existing M76 harness; no code change was
needed.

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

## Command

```text
conda run -n autodrift python -m autodrift.snapshot_bank_relocation \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m74_active_probe_near_miss_seeds.csv \
  --seed 8500 \
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
  --snapshot-relocation-lateral-offsets=-1,1 \
  --snapshot-relocation-half-widths 0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8 \
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
  --run-dir runs/m77_boundary_dense_width_strict_seed8500
```

## Result

| Run | Candidates | Strict Visible | Margin-Gap Rows | Accepted | Max Gap | Mean Visible Distance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| dense-width strict | 1344 | 448 | 52 | 0 | 0.105091 | 0.234060 |

M77 found much larger wrong-history margin gaps than M76, but the largest rows
are not valid self-identification evidence:

```text
normal history already collides
wrong history collides more deeply
```

The best strict-visible large-gap rows are collision-to-collision examples:

| Seed | Pair Rank | Body X | Body Y | Half Width | Source | Normal Margin | Wrong Margin | Gap |
| ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| 8119 | 4 | 11.0 | 1.0 | 1.6 | nominal | -0.003099 | -0.108190 | 0.105091 |
| 8119 | 1 | 11.0 | 1.0 | 1.6 | nominal | -0.003099 | -0.108163 | 0.105064 |

These are useful diagnostics but not pass rows because normal history does not
succeed and does not have positive margin.

## Near-Boundary Rows

M77 did create strict-visible rows with normal-history margin in `[0.0, 0.20]`,
but the wrong-history gap is too small or has the wrong sign.

Best perturbed near-boundary examples:

| Seed | Pair Rank | Body X | Body Y | Half Width | Normal Margin | Wrong Margin | Gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8108 | 3 | 12.0 | -1.0 | 1.1 | 0.143359 | 0.136069 | 0.007290 |
| 8108 | 3 | 12.0 | -1.0 | 1.2 | 0.030336 | 0.023947 | 0.006389 |
| 8108 | 3 | 11.0 | -1.0 | 0.9 | 0.162203 | 0.156054 | 0.006149 |
| 8108 | 3 | 11.0 | -1.0 | 1.0 | 0.051163 | 0.045765 | 0.005398 |

The pre-registered M77 margin-gap threshold was:

```text
min_margin_gap = 0.01
```

So none of these are accepted.

## Interpretation

M77 is negative.

What improved:

- dense width search can place some rows close to the clearance boundary;
- strict visible matching is preserved for many rows;
- collision-to-collision wrong-history gaps can be very large.

What failed:

- when normal history succeeds near the boundary, wrong history is only
  millimeters worse;
- when wrong history is much worse, normal history is already a collision;
- continuing to mine geometry-only snippets is likely low leverage.

## Next Step

M78 should stop treating mining alone as the main route. The next experiment
should implement an outcome-weighted intervention objective:

```text
use M76/M77 rows as weighted snippets
increase weight when wrong-history margin is worse
but train against outcome/value preference, not just replay frequency
keep M62/M67E retention gates as guards
```

This returns to the M67-F direction: make the policy learn that recurrent
history should affect risk and actions only when outcome evidence says it
matters.
