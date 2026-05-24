# M609 Boundary-Conditioned Source Miner Implementation

## Purpose

M609 implements and runs the boundary/risk-conditioned source miner designed by
M608.

Question:

```text
Can the full reconstructable M604 belief-only source pool produce near-boundary
rows suitable for a second grounded target-search smoke?
```

Scope:

```text
no action targets
no training
no PPO
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/boundary_conditioned_source_miner.py
tests/test_boundary_conditioned_source_miner.py
```

The miner:

1. reads the full M604 coupling table;
2. keeps reconstructable variants:
   `wrong_matched_history` and `delayed_history`;
3. filters to `candidate_for_grounding == true` and
   `capability_z_distance >= 0.10`;
4. removes duplicate physical source rows;
5. reconstructs BC5660 left snapshots on fresh/OOD configs;
6. runs an unchanged BC5660 normal-branch baseline continuation;
7. admits boundary rows by collision, margin window, or high baseline risk;
8. writes source, accepted boundary, rejected/far, and summary artifacts.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_conditioned_source_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --coupling-rows runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --include-variant wrong_matched_history \
  --include-variant delayed_history \
  --min-capability-z-distance 0.10 \
  --margin-window 0.50 \
  --risk-quantile 0.75 \
  --max-continuation-steps 80 \
  --device cpu \
  --run-dir runs/m609_boundary_conditioned_source_miner
```

## Artifacts

```text
runs/m609_boundary_conditioned_source_miner/summary.json
runs/m609_boundary_conditioned_source_miner/selected_source_pool.csv
runs/m609_boundary_conditioned_source_miner/source_rollouts.csv
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
runs/m609_boundary_conditioned_source_miner/rejected_far_rows.csv
```

## Results

| Metric | Value |
| --- | ---: |
| full M604 rows | `6776` |
| selected reconstructable source pool | `33` |
| source rollout rows | `33` |
| boundary source rows | `17` |
| rejected/far rows | `16` |
| baseline collision rows | `9` |
| baseline margin `<= 0.50` rows | `17` |
| baseline margin mean | `0.844532` |
| baseline margin median | `0.474526` |
| baseline margin min | `-0.191270` |
| baseline margin max | `3.415841` |
| risk threshold, 75th percentile | `10.021176` |

Boundary acceptance:

| Reason | Count |
| --- | ---: |
| baseline collision | `9` |
| baseline margin window | `8` |

Rejected rows:

| Reason | Count |
| --- | ---: |
| baseline far from boundary | `16` |

## Diversity

The boundary rows are source-diverse except for total row count:

| Metric | Value | Threshold |
| --- | ---: | ---: |
| rows | `17` | `>= 24` |
| unique physical pairs | `16` | `>= 8` |
| unique left seeds | `9` | `>= 8` |
| surfaces | `2` | `>= 2` |
| variants | `2` | `>= 2` |
| targets | `3` | `>= 2` |
| max physical-pair dominance | `0.117647` | `<= 0.25` |

`diversity_pass` is `false` only because the row count is below the desired
`24`-row threshold. This blocks optimizer admission and training corpus claims.
It does not block a limited no-training target-search diagnostic on these
boundary rows.

## Interpretation

M609 confirms the M607 diagnosis. The full source pool contains near-boundary
rows, but the usable boundary set is smaller than desired.

Supported claim:

```text
boundary-conditioned source screening is useful and produces auditable
near-boundary rows
```

Unsupported claim:

```text
there is already enough source diversity for an optimizer/training corpus
```

Therefore the next step should be a limited boundary-row target-search smoke,
not actor training.

## Contract Checks

```text
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
target_actions_written: false
```

## Decision

Decision:

```text
boundary_conditioned_source_miner_partial_admit_limited_target_smoke
```

Next:

```text
m610-boundary-conditioned-grounded-target-miner
```

M610 may run grounded target search on the `17` boundary rows, but any accepted
targets are diagnostic only until a later milestone either expands source
diversity or validates repeatability.
