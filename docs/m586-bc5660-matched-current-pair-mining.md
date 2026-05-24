# M586 BC5660 Matched-Current Pair Mining

## Purpose

M586 mines BC5660 matched-current pair surfaces for later delayed/wrong-history
intervention gates. It uses the two commands pre-registered in M585:

```text
fresh route seeds:   25560,25561,25562,25563
moderate-OOD seeds:  25660,25661,25662,25663
checkpoint:          runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
```

This milestone performs pair mining only:

```text
no history intervention rollout
no training
no PPO
no checkpoint promotion
```

## Commands

Fresh route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --probe-seeds 25560,25561,25562,25563 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
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
  --run-dir runs/m586_bc5660_matched_current_fresh_seed25560
```

Moderate-OOD:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_current_response_ambiguity \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --env-config configs/eval_m574_moderate_ood_l3.json \
  --probe-seeds 25660,25661,25662,25663 \
  --episodes 40 \
  --horizon-steps 15 \
  --sample-stride 3 \
  --max-samples 1200 \
  --nearest-k 12 \
  --match-feature-set current_response_context \
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
  --run-dir runs/m586_bc5660_matched_current_ood_seed25660
```

## Artifacts

Fresh route:

```text
runs/m586_bc5660_matched_current_fresh_seed25560/summary.json
runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv
runs/m586_bc5660_matched_current_fresh_seed25560/candidate_pairs.csv
runs/m586_bc5660_matched_current_fresh_seed25560/target_summary.csv
```

Moderate-OOD:

```text
runs/m586_bc5660_matched_current_ood_seed25660/summary.json
runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
runs/m586_bc5660_matched_current_ood_seed25660/candidate_pairs.csv
runs/m586_bc5660_matched_current_ood_seed25660/target_summary.csv
```

## Results

| surface | candidate pairs | accepted pairs | physical pairs | left steps | obstacle buckets | surface found |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| fresh route | 85092 | 666 | 192 | 15 | 14 | true |
| moderate-OOD | 73812 | 403 | 152 | 14 | 14 | true |

Accepted pairs by target:

| surface | braking decel | yaw response | lateral accel |
| --- | ---: | ---: | ---: |
| fresh route | 202 | 375 | 89 |
| moderate-OOD | 165 | 191 | 47 |

Pre-registered pass threshold:

```text
At least one surface:
  accepted pairs >= 60
  accepted physical pairs >= 10
  accepted left steps >= 5
  accepted source obstacle buckets >= 4

Preferred:
  both surfaces meet thresholds
```

Both surfaces pass, so M586 satisfies the preferred condition.

## Interpretation

BC5660 exposes source-diverse matched-current pair surfaces on both fresh route
and moderate-OOD distributions. This is the correct substrate for the next
history-intervention tests:

```text
same or very similar current response/context
different future response targets
candidate hidden histories available for delayed/wrong-history injection
```

M586 does not prove self-identification by itself. It only establishes that the
next gates have enough matched-current source coverage to run.

## Decision

```text
bc5660_matched_current_pair_mining_pass_admit_action_screen
```

M586 passes and admits M587 action-level history-intervention screening on both
surfaces. No checkpoint is promoted.

## Next

```text
M587: run matched_history_intervention_gate on the fresh-route and OOD pair surfaces.
```
