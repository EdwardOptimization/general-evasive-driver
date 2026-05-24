# M621 Tier-Aware Sequence Target Miner Rerun

## Purpose

M621 formally reruns the sequence target miner after M620 added source-tier
metadata propagation and accepted-candidate-set artifacts.

Question:

```text
Does the tier-aware miner preserve M617 selected-sequence behavior while adding
the evidence needed for candidate-set audit?
```

Answer:

```text
Yes. M621 reproduces the M617 selected-sequence result and writes the new
accepted_candidate_sequences.csv artifact with source-tier metadata.
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
  --run-dir runs/m621_tier_aware_sequence_target_miner
```

## Parity With M617

| Metric | M617 | M621 |
| --- | ---: | ---: |
| source rows | `30` | `30` |
| candidate rollouts | `10440` | `10440` |
| selected accepted sequences | `6` | `6` |
| unaccepted rows | `24` | `24` |
| accepted margin improvement mean | `0.056784` | `0.056784` |
| accepted margin improvement min | `0.020817` | `0.020817` |
| accepted margin improvement max | `0.093048` | `0.093048` |
| best unaccepted margin improvement | `0.025914` | `0.025914` |

The tier-aware code does not alter selected-sequence behavior.

## New Candidate-Set Evidence

New artifact:

```text
runs/m621_tier_aware_sequence_target_miner/accepted_candidate_sequences.csv
```

It contains:

```text
accepted candidate sequences: 189
physical pairs: 5
left seeds: 4
surfaces: 2
variants: 2
targets: 3
```

Accepted candidate family counts:

| Family | Count |
| --- | ---: |
| decay_pulse | `86` |
| constant_delta | `64` |
| steer_then_brake | `22` |
| brake_release_then_steer | `17` |

Accepted candidate tier counts:

| Tier | Count |
| --- | ---: |
| support_boundary | `98` |
| near_boundary | `89` |
| core_boundary | `2` |

Accepted candidate sequence length counts:

| Length | Count |
| --- | ---: |
| K=5 | `108` |
| K=3 | `81` |

Selected accepted sequence tier counts:

| Tier | Count |
| --- | ---: |
| near_boundary | `3` |
| support_boundary | `2` |
| core_boundary | `1` |

## Artifact Checks

These files now include source metadata:

```text
accepted_sequences.csv
accepted_candidate_sequences.csv
unaccepted_rows.csv
```

Required columns:

```text
source_tier
expansion_reason
original_m609_boundary
m613_accepted_sequence
```

All are present.

## Interpretation

M621 confirms the M620 artifact change is behavior-preserving and useful.

Important distinction:

```text
candidate-level family diversity exists
source-level diversity remains narrow
```

The `189` accepted candidates should not be treated as `189` independent source
examples. They cover only:

```text
5 physical pairs
4 left seeds
```

Therefore optimizer admission remains blocked.

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
tier_aware_sequence_rerun_pass_admit_candidate_audit
```

Next blocker:

```text
m622-tier-aware-sequence-candidate-audit
```
