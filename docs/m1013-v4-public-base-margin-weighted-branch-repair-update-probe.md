# M1013 V4 Public Base Margin-Weighted Branch Repair Update Probe

## Purpose

M1013 implements the M1012 objective-only actor_mean repair probe.

This milestone trains only `actor_mean` under an exact objective. It does not
run PPO, run replay gates, use private holdout, change actor inputs, or promote
a checkpoint.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.margin_weighted_branch_repair_update_probe \
  --checkpoint runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt \
  --corpus runs/m997_v4_public_base_temporal_sequence_corpus_export/temporal_sequence_corpus.npz \
  --metadata runs/m997_v4_public_base_temporal_sequence_corpus_export/metadata.csv \
  --base-summary runs/m1000_v4_public_base_temporal_sequence_objective_evaluator/summary.json \
  --m267-corpus runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv \
  --m1004-replay-rows runs/m1004_v4_public_base_temporal_sequence_update_public_replay_gate/candidate_preflight/m1002_temporal_a0_01/boundary_replay_rows.csv \
  --run-dir runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe \
  --device auto \
  --active-rows 6,15,11,16 \
  --max-continuation-steps 60 \
  --margin-floor 1e-4 \
  --epochs 200 \
  --seed 1013 \
  --lr 1e-4 \
  --grad-clip-norm 1.0 \
  --alphas 0.0025,0.005,0.01,0.02,0.05,0.1,0.2,0.5,1.0 \
  --lambda-wrong-trust-values 0.001,0.003,0.01,0.03
```

## Result

```text
result_class: margin_weighted_branch_repair_update_branch_trust_blocked
failure_types: proof_washout
exact_candidate_count: 10
exact_and_branch_candidate_count: 0
raw_changed_parameter_names: actor_mean.bias, actor_mean.weight
raw_non_actor_changed: false
ppo_used: false
promoted: false
```

The update machinery is valid: only `actor_mean` changed, training metrics were
finite, and no PPO/promotion/private holdout path was used. The result is
negative because exact temporal candidates still leave the M1011 trust region.

## Candidate Summary

| lambda_wrong_trust | exact candidates | trust-gate candidates | joint candidates |
| ---: | ---: | ---: | ---: |
| 0.001 | 3 | 4 | 0 |
| 0.003 | 2 | 4 | 0 |
| 0.010 | 3 | 3 | 0 |
| 0.030 | 2 | 4 | 0 |

Best exact candidate per coefficient:

| lambda | alpha | total improvement | branch trust loss | row 6 | row 15 | row 16 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.001 | 1.0 | 0.006475 | 33.123423 | 11.672500 | 18.047144 | 1.961625 |
| 0.003 | 1.0 | 0.004436 | 52.804807 | 22.549787 | 29.069977 | 0.294085 |
| 0.010 | 1.0 | 0.005243 | 217.969845 | 83.957520 | 122.931904 | 3.505045 |
| 0.030 | 1.0 | 0.003741 | 27.941453 | 11.095083 | 15.390196 | 0.569695 |

Best trust-safe rows are all very small-alpha points, but they do not reach the
temporal exact improvement threshold. Example:

```text
lambda 0.030, alpha 0.0025:
  total improvement: 0.00000951
  branch trust loss: 0.000165
  exact_gate_pass: false
  branch_gate_pass: true
```

## Interpretation

M1013 separates the conflict cleanly:

```text
temporal exact objective can still improve;
M1011 branch trust can remain safe at tiny alpha;
no actor_mean-only direction found in this recipe improves temporal exact loss
enough while staying branch-safe.
```

This should not be repaired by immediately relaxing M1011 trust gates. The
known failing M1002 alpha `0.01` already proof-washes rows `6` and `15`, so any
threshold relaxation needs an audit first.

The likely next questions are:

```text
1. Is the branch trust threshold too strict relative to closed-loop replay, or
   is it correctly detecting a real active constraint?

2. Does the actor_mean-only surface lack enough degrees of freedom to improve
   temporal exact rows while holding rows 6 and 15 fixed?

3. Did large lambda values create optimizer instability or branch-loss
   oscillation rather than a useful constrained direction?

4. Would a projection/line-search repair from a temporal direction be cleaner
   than joint scalar training?
```

## Decision

```text
margin_weighted_branch_repair_update_branch_trust_blocked_route_to_audit
```

Next:

```text
m1014-v4-public-base-margin-weighted-repair-failure-audit
```
