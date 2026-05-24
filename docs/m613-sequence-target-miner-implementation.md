# M613 Sequence Target Miner Implementation

## Purpose

M613 implements and runs the diagnostic short-horizon sequence target miner
designed by M612.

Question:

```text
Can a bounded structured action-sequence prefix improve margin/risk on M609
boundary rows where single first-action overrides failed?
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
src/autodrift/sequence_target_miner.py
tests/test_sequence_target_miner.py
```

The miner:

1. reads M609 `boundary_source_rows.csv`;
2. reconstructs BC5660 snapshots;
3. generates structured action-sequence candidates around the base policy;
4. executes the sequence prefix open-loop while updating recurrent hidden state
   from observations;
5. continues under unchanged BC5660;
6. applies the unchanged M606/M610 margin/risk acceptance thresholds;
7. writes all candidates, accepted sequences, unaccepted rows, summary, and
   optional NPZ corpus.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.sequence_target_miner \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --boundary-source-rows runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv \
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
  --run-dir runs/m613_sequence_target_miner
```

## Artifacts

```text
runs/m613_sequence_target_miner/summary.json
runs/m613_sequence_target_miner/selected_boundary_source_rows.csv
runs/m613_sequence_target_miner/sequence_candidates.csv
runs/m613_sequence_target_miner/accepted_sequences.csv
runs/m613_sequence_target_miner/unaccepted_rows.csv
runs/m613_sequence_target_miner/sequence_target_corpus.npz
```

## Results

| Metric | Value |
| --- | ---: |
| source rows | `17` |
| candidate rollouts | `5916` |
| accepted candidate rows | `2` |
| selected accepted sequences | `1` |
| unaccepted source rows | `16` |
| max candidate improvement | `0.025914` |
| accepted margin improvement | `0.020817` |
| accepted family | `constant_delta` |
| accepted sequence length | `5` |

Candidate rejection counts:

| Reason | Count |
| --- | ---: |
| outside sequence trust region | `2594` |
| candidate collision | `1750` |
| insufficient margin or risk improvement | `1570` |

Accepted candidate reasons:

| Reason | Count |
| --- | ---: |
| margin improved | `2` |

The selected accepted sequence:

| Field | Value |
| --- | --- |
| source index | `7` |
| surface | `fresh` |
| variant | `delayed_history` |
| target | `future_braking_deceleration` |
| left seed / step | `25567 / 3` |
| right seed / step | `25587 / 3` |
| sequence length | `5` |
| family | `constant_delta` |
| delta | `+0.08 steer`, `0 throttle`, `0 brake` |
| baseline margin | `0.274439` |
| target margin | `0.295255` |
| margin improvement | `0.020817` |
| sequence mean L2 | `0.08` |
| sequence max L2 | `0.08` |

`sequence_target_corpus.npz` contains one padded sequence row with fields:

```text
observation
normal_hidden
variant_hidden
target_action_sequence
normal_base_action_sequence
sequence_mask
variant_base_action
weight
row_id
source_index
sequence_length
```

## Interpretation

M613 is a diagnostic positive result.

Compared with M610, the sequence prefix crosses the unchanged `0.02` margin
threshold where single first-action targets did not. This supports the M611
diagnosis that the blocker was first-action locality / myopia.

However, the result is narrow:

```text
accepted selected sequences: 1
accepted physical pairs: 1
accepted left seeds: 1
accepted surfaces: 1
accepted variants: 1
accepted targets: 1
```

Therefore this is not a training corpus, not a driver improvement claim, and
not optimizer admission. It only justifies a follow-up audit and either
source-diversity expansion or repeatability checks.

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
sequence_target_miner_diagnostic_positive_admit_audit
```

Next:

```text
m614-sequence-target-mining-audit
```
