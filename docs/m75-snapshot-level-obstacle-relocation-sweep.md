# M75 Snapshot-Level Obstacle Relocation Sweep

M74 showed that reset-level obstacle geometry sweeps destroy or move the
active-probe history that created the M73 margin signal. M75 changes the search
surface:

```text
collect active-probe decision snapshots
deep-copy the snapshot env and recurrent hidden state
mutate only obstacle body-frame position and half-width
rebuild the current observation from the copied env
replay normal history and wrong matched history
```

The goal is not to make the task easier globally. The goal is to preserve the
same ego state, actuator state, action-response history, and recurrent hidden
state while sweeping only the obstacle boundary.

## Code Changes

`autodrift.outcome_sensitive_corpus` now supports snapshot relocation:

```text
--snapshot-relocation-distances
--snapshot-relocation-lateral-offsets
--snapshot-relocation-half-widths
```

Implementation details:

- `relocate_obstacle_snapshot(...)` deep-copies a `DecisionSnapshot`;
- obstacle position is placed in the current ego body frame;
- obstacle half-width and scenario metadata are recomputed;
- current clearance, collision state, info, and observation are rebuilt;
- `active_probe_*` metadata is preserved;
- existing replay, wrong-history, summary, and corpus selection logic is reused.

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  conda run -n autodrift pytest -q tests/test_outcome_sensitive_corpus.py
```

Result:

```text
11 passed
```

Final validation:

```text
git diff --check
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 conda run -n autodrift pytest -q
```

Result:

```text
207 passed
```

## Main Strict Sweep

Base command shape:

```text
conda run -n autodrift python -m autodrift.outcome_sensitive_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv experiments/m74_active_probe_near_miss_seeds.csv \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 16 \
  --target-obstacle-distances 6,8,10 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.25 \
  --probe-brake-level 0.20 \
  --probe-period-steps 20 \
  --min-margin-gap 0.01 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 0
```

The first strict smoke used centered relocated obstacles:

```text
--snapshot-relocation-distances 5,6,7,8,9,10,11,12
--snapshot-relocation-lateral-offsets 0
--snapshot-relocation-half-widths 0.8,1.0,1.2,1.4
--run-dir runs/m75_snapshot_relocation_smoke_seed8300
```

Result:

| Run | Candidates | Strict Visible | Margin-Gap Rows | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| centered strict | 288 | 64 | 103 | 0 | 0.122641 |

Interpretation: snapshot relocation preserved a much stronger margin signal than
M74, but the perturbed branch was usually collision-to-collision under the
strict rows.

## Lateral Sweep

The second strict sweep added lateral offsets:

```text
--snapshot-relocation-distances 7,8,9,10,11,12
--snapshot-relocation-lateral-offsets=-2,-1,0,1,2
--snapshot-relocation-half-widths 0.8,1.0,1.2
--run-dir runs/m75_snapshot_relocation_lateral_seed8301
```

Result:

| Run | Candidates | Strict Visible | Source-Outcome Rows | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| lateral strict | 810 | 180 | 2 | 0 | 0.227224 |

The two source-outcome rows had valid perturbed normal margins and
wrong-history margin loss, but failed visible matching:

| Seed | Source Target | Body X | Body Y | Half Width | Response Dist | Context Dist | Perturbed Margin Gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8119 | 6.0 | 12.0 | -1.0 | 1.0 | 0.368585 | 0.846937 | 0.015229 |
| 8119 | 6.0 | 11.0 | -1.0 | 0.8 | 0.368585 | 0.846937 | 0.012997 |

The strict threshold was:

```text
max_response_distance = 0.35
max_context_distance = 0.05
```

So these are useful near misses, not accepted snippets.

## Mid-Friction Diagnostic

To test whether the low-friction branch was too hard, M75 repeated the lateral
sweep with:

```text
--perturbed-friction-mu-range 0.35,0.45
--run-dir runs/m75_snapshot_relocation_mid_friction_seed8302
```

Result:

| Run | Candidates | Strict Visible | Source-Outcome Rows | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| mid-friction strict | 810 | 180 | 1 | 0 | 0.228434 |

This did not solve the strict matching issue.

## Relaxed Diagnostic

M75 also ran a deliberately relaxed visible-match diagnostic:

```text
--max-visible-distance 1.0
--max-response-distance 0.40
--max-context-distance 0.90
--run-dir runs/m75_snapshot_relocation_relaxed_seed8303
```

Result:

| Run | Candidates | Relaxed Visible | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: |
| relaxed lateral | 810 | 720 | 2 | 0.227224 |

Accepted relaxed snippets:

| Seed | Source Target | Body X | Body Y | Half Width | Perturbed Normal Margin | Perturbed Wrong Margin | Gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 8119 | 6.0 | 12.0 | -1.0 | 1.0 | 0.095783 | 0.080554 | 0.015229 |
| 8119 | 6.0 | 11.0 | -1.0 | 0.8 | 0.130349 | 0.117352 | 0.012997 |

This is not a pass. It proves the relocation harness can expose
wrong-history margin loss when visibility thresholds are relaxed.

## Target Refinement

The final strict diagnostic refined source snapshot target distance around the
relaxed near misses:

```text
--target-obstacle-distances 6,6.5,7,7.5,8,8.5,9,9.5,10
--snapshot-relocation-distances 11,12
--snapshot-relocation-lateral-offsets=-1
--snapshot-relocation-half-widths 0.8,1.0,1.2
--run-dir runs/m75_snapshot_relocation_target_refine_seed8304
```

Result:

| Run | Candidates | Strict Visible | Source-Outcome Rows | Accepted | Max Gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| target-refine strict | 162 | 12 | 7 | 0 | 0.020358 |

As source target distance moves from `6.0` toward `7.5`, visible distances
improve and the outcome signal weakens. At target `10.0`, strict matching passes
but the wrong-history margin deltas are only millimeter-scale.

## Conclusion

M75 is an infrastructure pass and a negative strict gate result.

What improved:

- snapshot relocation preserves the active-probe history better than M74;
- margin-gap rows are much stronger than reset-level geometry sweeps;
- relaxed diagnostics can produce valid wrong-history margin-loss snippets.

What still fails:

- strict visible-state matching rejects the useful source-outcome rows;
- strict visible rows have weak or invalid outcome differences;
- current single-target snapshot pairing is too brittle.

The next step should collect a bank of active-probe snapshots per episode and
pair nominal/perturbed snapshots by actual visible-state distance, not by a
shared target obstacle distance.

## Next Step

M76 should implement a snapshot-bank visible matcher:

```text
collect many active-probe snapshots per condition
pair nominal and perturbed snapshots by response/context distance
then apply snapshot-level obstacle relocation
rank by visible match, normal-success margin, and wrong-history margin loss
```

This directly targets the M75 blocker: outcome-sensitive rows exist, but the
current same-target pairing does not make them strict visible matches.
