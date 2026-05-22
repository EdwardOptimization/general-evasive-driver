# M192 Current-Best Proof-Surface Refresh

M191 validated M189 on fresh behavior seeds and existing M183 replay surfaces,
but the evidence was still inherited from the same M183 boundary rows used for
guarded updates. M192 refreshes the proof surface without training or changing
actor inputs.

Current checkpoint family:

```text
m184_s20   runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt
m188_5191  runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt
m189_5193  runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt
```

## Matched-Current Mining

Artifact:

```text
runs/m192_current_family_matched_current_seed9520
```

Command uses fresh probe seeds `9520,9521,9522,9523` and the same P0
zero-obstacle-relvel actor input profile:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy m184_s20=runs/m184_m168_actor_coupling_anchor100_s20_seed9840/optimized_checkpoint.pt \
  --checkpoint-policy m188_5191=runs/ppo_m188_stage2_from_m185_seed5191/checkpoint.pt \
  --checkpoint-policy m189_5193=runs/ppo_m189_stage3_from_m188_seed5193/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --probe-seeds 9520,9521,9522,9523 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --max-visible-quantile 0.05 \
  --min-target-z-delta 1.0 \
  --max-pairs-per-target 320 \
  --max-pairs-per-physical-pair 1 \
  --max-pairs-per-left-step 20 \
  --max-pairs-per-source-obstacle-bucket 40 \
  --obstacle-distance-bucket-width 5.0 \
  --obstacle-lateral-bucket-width 1.0 \
  --min-accepted-pairs 60 \
  --device cpu \
  --run-dir runs/m192_current_family_matched_current_seed9520
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 276369 |
| Accepted pairs | 2817 |
| Accepted physical pairs | 283 |
| Accepted left steps | 31 |
| Accepted obstacle buckets | 19 |
| Surface found | true |

Accepted by target:

| Target | Rows |
| --- | ---: |
| future braking deceleration | 2330 |
| future lateral accel response | 234 |
| future yaw response | 253 |

## Direct Outcome Gate

Artifact:

```text
runs/m192_current_family_outcome_seed9520
```

Raw continuation remains outcome-neutral for wrong-history:

| Variant | Rows | Success drops | Normal-better rows | Max margin gap | Mean margin gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| wrong matched history | 2817 | 0 | 0 | 0.013937 | -0.000254 |
| reset hidden | 2817 | 0 | 552 | 0.155449 | 0.009117 |
| zero current response | 2817 | 0 | 622 | 0.061539 | 0.004191 |
| zero action history | 2817 | 0 | 0 | 0.006677 | -0.002302 |
| delayed history | 2817 | 0 | 75 | 0.054524 | -0.001140 |

This is consistent with M178 and M182: current-state matched pairs are
response-sensitive, but raw obstacle geometry is usually not tight enough to
turn the action difference into failure.

## Boundary Relocation

Artifact:

```text
runs/m192_current_family_boundary_surface_seed9520
```

Unlike M182, M192 runs the full intervention set at the boundary-relocation
stage:

```text
wrong_matched_history
reset_hidden
zero_current_response
zero_action_history
delayed_history
```

| Metric | Value |
| --- | ---: |
| Candidate pairs | 2817 |
| Boundary replay rows | 63990 |
| Accepted wrong-history rows | 131 |
| Accepted wrong-history source pairs | 87 |
| Wrong-history success drops | 131 |
| Accepted reset rows | 3389 |
| Accepted zero-current rows | 3455 |
| Surface found | true |

Accepted wrong-history rows by checkpoint:

| Checkpoint | Rows |
| --- | ---: |
| m184_s20 | 39 |
| m188_5191 | 44 |
| m189_5193 | 48 |

Accepted wrong-history rows by target:

| Target | Rows |
| --- | ---: |
| future braking deceleration | 119 |
| future yaw response | 12 |

## Robustness Gate

Artifact:

```text
runs/m192_current_family_boundary_robustness_seed9520
```

The robustness gate is stricter than M182 on checkpoint coverage: it requires
all three current-family checkpoints to appear.

| Gate metric | Value | Threshold | Pass |
| --- | ---: | ---: | --- |
| Accepted wrong rows | 131 | >= 40 | true |
| Physical pairs | 11 | >= 10 | true |
| Left steps | 6 | >= 5 | true |
| Checkpoints | 3 | >= 3 | true |
| Targets | 2 | >= 2 | true |
| Normal-margin buckets | 2 | >= 2 | true |
| Success-drop fraction | 1.0 | >= 1.0 | true |
| Max rows per physical pair fraction | 0.183206 | <= 0.25 | true |
| Control accepted rows | 0 | <= 0 | true |

Decision:

```text
admit_boundary_wrong_history_objective
```

## Decision

M192 is positive. It refreshes the proof surface beyond M183 and shows that the
current M184/M188/M189 checkpoint family still has a source-diverse
wrong-history boundary outcome signal.

What this proves:

- M189 is not only retaining the old M183 rows;
- fresh matched-current pairs can still be mined under the current P0 input
  contract;
- wrong-history intervention can be turned into real near-boundary success
  drops;
- the accepted rows are not dominated by one physical pair or one checkpoint.

What it does not prove yet:

- the refreshed rows are not yet converted into a replay-aligned objective;
- no actor update or stage4 PPO has been justified from this surface;
- lateral-response coverage is still weak in the accepted wrong-history rows.

Next step:

```text
m193-current-family-boundary-objective-sanity
```

M193 should convert the M192 accepted rows into boundary-outcome corpora,
starting with current-best M189, and run objective plus replay sanity before any
guarded actor update or PPO continuation.
