# M610 Boundary-Conditioned Grounded Target Miner

## Purpose

M610 runs a limited no-training grounded target search on the `17` M609
boundary-conditioned source rows.

Question:

```text
Does restricting target search to near-boundary source rows produce simulator-
grounded first-action targets that M606 could not find?
```

Scope:

```text
diagnostic only
no training
no PPO
no checkpoint promotion
no optimizer admission
```

## Implementation

Added:

```text
src/autodrift/boundary_conditioned_grounded_target_miner.py
tests/test_boundary_conditioned_grounded_target_miner.py
```

The wrapper reads:

```text
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
```

and reuses the M606 first-action local search, acceptance logic, candidate
logging, accepted-target logging, unaccepted-row logging, and optional target
corpus writer. Outputs are explicitly marked `diagnostic_only = true`.

## Command

The final run used the same `80`-step continuation horizon as M609 boundary
source screening:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.boundary_conditioned_grounded_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --boundary-source-rows runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --steer-deltas=-0.08,-0.04,-0.02,0,0.02,0.04,0.08 \
  --throttle-deltas=-0.06,-0.03,0,0.03 \
  --brake-deltas=-0.08,-0.04,-0.02,0,0.02,0.04,0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --max-action-l2 0.10 \
  --max-continuation-steps 80 \
  --device cpu \
  --run-dir runs/m610_boundary_conditioned_grounded_target_miner
```

## Artifacts

```text
runs/m610_boundary_conditioned_grounded_target_miner/summary.json
runs/m610_boundary_conditioned_grounded_target_miner/selected_boundary_source_rows.csv
runs/m610_boundary_conditioned_grounded_target_miner/target_candidates.csv
runs/m610_boundary_conditioned_grounded_target_miner/accepted_targets.csv
runs/m610_boundary_conditioned_grounded_target_miner/unaccepted_rows.csv
```

No `target_corpus.npz` was written because there were no accepted targets.

## Results

| Metric | Value |
| --- | ---: |
| source rows | `17` |
| candidate rollouts | `3332` |
| accepted targets | `0` |
| unaccepted rows | `17` |
| max candidate margin improvement | `0.017662` |
| max candidate risk improvement | `0.017662` |
| best trust-region margin improvement | `0.015549` |
| diagnostic only | `true` |
| optimizer admission | `false` |

Rejection counts:

| Reason | Count |
| --- | ---: |
| candidate collision | `1443` |
| insufficient margin or risk improvement | `1283` |
| outside action trust region | `606` |

Trust-region what-if:

| Margin threshold | Candidate count | Source rows |
| --- | ---: | ---: |
| `0.005` | `42` | `1` |
| `0.010` | `16` | `1` |
| `0.015` | `0` | `0` |
| `0.020` | `0` | `0` |

The best candidate overall is outside the `0.10` action trust region. Inside
the trust region, no row reaches even `0.015` margin improvement.

## Interpretation

M610 is a stronger negative result than M606.

M606 could have failed because the source rows were too far from a boundary.
M609 fixed that by selecting near-boundary rows. M610 still finds zero accepted
first-action targets under the same action trust region and pre-registered
margin/risk thresholds.

Supported diagnosis:

```text
single first-action local override is too weak or too myopic for this branch
```

Rejected explanations:

```text
M606 failed only because source rows were far from boundary
M606 failed only because the continuation horizon was too short
M606 failed only because accepted rows were hidden by logging
```

The next step should be an audit and then a sequence / short-horizon target
design, not immediate actor training.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
```

## Decision

Decision:

```text
boundary_conditioned_target_miner_negative_admit_sequence_audit
```

Next:

```text
m611-boundary-target-mining-audit
```
