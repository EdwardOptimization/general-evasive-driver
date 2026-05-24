# M617 Expanded Sequence Target Miner

## Purpose

M617 repeats the M613 diagnostic sequence target miner on the M616 expanded
source table.

Question:

```text
Does the M613 one-sequence signal repeat when source rows expand from 17 to 30?
```

Scope:

```text
no actor training
no PPO
no checkpoint promotion
no optimizer admission
```

## Command

Executed:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.sequence_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --boundary-source-rows runs/m616_expanded_sequence_source_miner/expanded_sequence_source_rows.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --sequence-lengths 3,5 \
  --family constant_delta \
  --family decay_pulse \
  --family brake_release_then_steer \
  --family steer_then_brake \
  --steer-deltas=-0.08,-0.04,0,0.04,0.08 \
  --throttle-deltas=-0.06,0,0.03 \
  --brake-deltas=-0.08,-0.04,0,0.04,0.08 \
  --per-step-action-l2 0.10 \
  --sequence-mean-l2-limit 0.08 \
  --sequence-max-l2-limit 0.10 \
  --max-delta-delta-l2-limit 0.08 \
  --min-margin-improvement 0.02 \
  --min-risk-improvement 0.05 \
  --max-continuation-steps 80 \
  --device cpu \
  --run-dir runs/m617_expanded_sequence_target_miner
```

The command intentionally keeps M613 sequence lengths, families, trust regions,
and acceptance thresholds unchanged.

## Results

Artifacts:

```text
runs/m617_expanded_sequence_target_miner/summary.json
runs/m617_expanded_sequence_target_miner/sequence_candidates.csv
runs/m617_expanded_sequence_target_miner/accepted_sequences.csv
runs/m617_expanded_sequence_target_miner/unaccepted_rows.csv
runs/m617_expanded_sequence_target_miner/sequence_target_corpus.npz
```

Summary:

| Metric | M613 | M617 |
| --- | ---: | ---: |
| source rows | `17` | `30` |
| candidate rollouts | `5916` | `10440` |
| selected accepted sequences | `1` | `6` |
| unaccepted source rows | `16` | `24` |
| accepted margin improvement mean | `0.020817` | `0.056784` |
| accepted margin improvement max | `0.020817` | `0.093048` |
| sequence target corpus rows | `1` | `6` |

M617 is a clear repeatability improvement over M613, but it still misses the
pre-registered objective-admission breadth target.

## Accepted Sequence Diversity

Accepted diversity:

| Metric | Value |
| --- | ---: |
| accepted sequences | `6` |
| physical pairs | `5` |
| left seeds | `4` |
| surfaces | `2` |
| variants | `2` |
| targets | `3` |
| max physical-pair dominance | `0.333333` |

The accepted rows are not broad enough for optimizer admission:

```text
accepted sequences target: >= 8
accepted physical pairs target: >= 6
accepted left seeds target: >= 6
```

All selected accepted sequences are:

```text
family: constant_delta
sequence_length: 5
delta: +0.08 steer, 0 throttle, 0 brake
```

That is useful diagnostic evidence, but it is too action-mode narrow for a
training objective.

## Accepted Rows

Joined with M616 source tiers:

| Source | Tier | Surface | Variant | Target | Margin Improvement |
| ---: | --- | --- | --- | --- | ---: |
| `5` | near_boundary | fresh | delayed_history | future_lateral_accel_response | `0.035234` |
| `7` | core_boundary | fresh | delayed_history | future_braking_deceleration | `0.020817` |
| `13` | support_boundary | fresh | delayed_history | future_yaw_response | `0.093048` |
| `14` | support_boundary | fresh | delayed_history | future_yaw_response | `0.093048` |
| `20` | near_boundary | ood | delayed_history | future_yaw_response | `0.049279` |
| `32` | near_boundary | ood | wrong_matched_history | future_yaw_response | `0.049279` |

Tier counts:

```text
core_boundary: 1
near_boundary: 3
support_boundary: 2
```

Only one accepted row is from the original M609 core boundary set that was
already accepted by M613. The expansion added near/support rows with meaningful
sequence improvements, which supports the M615 expansion design.

## Unaccepted Rows

Top remaining near misses:

| Source | Surface | Variant | Target | Best Improvement | Rejection |
| ---: | --- | --- | --- | ---: | --- |
| `1` | ood | delayed_history | future_yaw_response | `0.025914` | outside_sequence_trust_region |
| `15` | fresh | delayed_history | future_lateral_accel_response | `0.020958` | candidate_collision |
| `30` | ood | wrong_matched_history | future_braking_deceleration | `0.019548` | outside_sequence_trust_region |

The main blocker remains close to M613:

```text
outside_sequence_trust_region: 4555 candidates
candidate_collision: 1750 candidates
insufficient_margin_or_risk_improvement: 3946 candidates
```

## Interpretation

M617 supports the sequence-target direction:

```text
M613: one accepted sequence
M617: six accepted sequences over expanded rows
```

But M617 does not yet support training:

```text
accepted row count below target
physical-pair count below target
left-seed count below target
selected action mode is one-sided constant +steer
```

The next step should be an audit, not an optimizer step.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
```

## Decision

Decision:

```text
expanded_sequence_target_miner_diagnostic_positive_admit_audit
```

Next blocker:

```text
m618-expanded-sequence-target-mining-audit
```
