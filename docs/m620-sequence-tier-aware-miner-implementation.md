# M620 Sequence Tier-Aware Miner Implementation

## Purpose

M620 implements the M619 artifact-governance step for sequence target mining.

Goal:

```text
make sequence target artifacts source-tier aware and accepted-candidate-set aware
```

Scope:

```text
no actor training
no PPO
no checkpoint promotion
no optimizer admission
no target threshold change
no trust-region change
```

## Implementation

Changed:

```text
src/autodrift/sequence_target_miner.py
tests/test_sequence_target_miner.py
```

New optional source metadata fields:

```text
source_tier
expansion_reason
original_m609_boundary
m613_accepted_sequence
```

When present in source rows, these fields now propagate into:

```text
sequence_candidates.csv
accepted_candidate_sequences.csv
accepted_sequences.csv
unaccepted_rows.csv
```

Older source rows without these fields remain supported; metadata columns are
written as blank values.

New artifact:

```text
accepted_candidate_sequences.csv
```

This contains every accepted candidate rollout, not only the selected
best-per-source sequence.

## Summary Additions

The sequence miner summary now includes:

```text
accepted_candidate_sequences
accepted_candidate_diversity
accepted_candidate_counts_by_family
accepted_candidate_counts_by_tier
accepted_candidate_counts_by_sequence_length
accepted_sequence_counts_by_tier
accepted_candidate_sequences_csv
```

This separates:

```text
selected best-per-source sequence diversity
accepted candidate-set diversity
```

The selected sequence corpus remains unchanged and still contains only the
best sequence per accepted source row.

## Focused Tests

Executed:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_sequence_target_miner.py \
  tests/test_expanded_sequence_source_miner.py
```

Result:

```text
18 passed
```

## Real Smoke

Executed a tier-aware smoke on the M616 expanded source table:

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
  --run-dir runs/m620_tier_aware_sequence_target_miner_smoke
```

Result:

| Metric | Value |
| --- | ---: |
| candidate rollouts | `10440` |
| accepted candidate sequences | `189` |
| selected accepted sequences | `6` |
| unaccepted rows | `24` |
| accepted candidate physical pairs | `5` |
| accepted candidate left seeds | `4` |
| accepted selected physical pairs | `5` |
| accepted selected left seeds | `4` |

Accepted candidate counts:

| Dimension | Counts |
| --- | --- |
| family | decay_pulse `86`, constant_delta `64`, steer_then_brake `22`, brake_release_then_steer `17` |
| tier | support_boundary `98`, near_boundary `89`, core_boundary `2` |
| sequence length | K=5 `108`, K=3 `81` |

Selected accepted sequence tier counts:

```text
near_boundary: 3
support_boundary: 2
core_boundary: 1
```

## Interpretation

M620 confirms the M618 diagnosis:

```text
candidate-level family diversity exists
source-level diversity remains narrow
```

The 189 accepted candidates should not be treated as 189 independent training
examples. They still cover only:

```text
5 physical pairs
4 left seeds
```

So optimizer admission remains blocked.

## Contract Checks

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
target_acceptance_thresholds_changed: false
trust_regions_changed: false
```

## Decision

Decision:

```text
sequence_tier_aware_miner_pass_admit_rerun
```

Next blocker:

```text
m621-tier-aware-sequence-target-miner-rerun
```
