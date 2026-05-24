# M674 Response-Amplification Actor-Coupling Implementation

## Purpose

M674 implements the conservative actor-coupling probe designed in M673:

```text
base actor: frozen BC5660
trainable module: residual sequence head only
feature view: fused_plus_next_hidden
execution model: execute only first residual in closed loop
PPO: forbidden
promotion: forbidden
```

The milestone tests whether M671's positive shadow evidence can become an
exact-gated deployable residual wrapper without changing the base actor.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.response_amplification_actor_coupling \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --shadow-corpus runs/m671_response_amplification_shadow/shadow_corpus.npz \
  --metadata runs/m671_response_amplification_shadow/shadow_metadata.csv \
  --view fused_plus_next_hidden \
  --seeds 6740,6741,6742 \
  --alphas 0.02,0.05,0.10,0.20,0.50,1.00 \
  --target-gap 0.010 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --device cpu \
  --run-dir runs/m674_response_amplification_actor_coupling
```

## Artifacts

```text
runs/m674_response_amplification_actor_coupling/summary.json
runs/m674_response_amplification_actor_coupling/alpha_summary.csv
runs/m674_response_amplification_actor_coupling/seed_view_summary.csv
runs/m674_response_amplification_actor_coupling/train_metrics.csv
```

Residual-head checkpoints are written under each seed directory. No base actor
checkpoint is written.

## Implementation Cleanliness

M674 is implementation-clean:

```text
rows:                          648
source_count:                  216
residual_head_checkpoint_count: 3
actor_parameters_changed:      false
base_actor_checkpoint_written: false
ppo_used:                      false
promoted:                      false
```

## Exact Gate Result

M674 fails the exact actor-coupling gate:

```text
actor_coupling_exact_passed: false
passed_seed_count:           0
best_selected_alpha:         0.0
```

No seed has a nonzero alpha satisfying both normal first-action drift and
wrong-history sequence-gap thresholds.

## Alpha Conflict

The failure is structured. At high alpha, the residual sequence gap is strong
but first-action normal drift is too large. At lower alpha, first-action drift
is acceptable but the wrong-history sequence gap is too small.

Source-heldout metrics:

| seed | alpha | pass | normal mean | normal p95 | gap mean | gap p10 | ratio | first drift p95 |
| ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 6740 | 0.50 | false | 0.001197 | 0.002030 | 0.006059 | 0.004262 | 2.108998 | 0.004860 |
| 6740 | 1.00 | false | 0.002394 | 0.004061 | 0.012119 | 0.008524 | 4.217997 | 0.009719 |
| 6741 | 0.50 | false | 0.001329 | 0.002237 | 0.006206 | 0.004238 | 2.160026 | 0.004702 |
| 6741 | 1.00 | false | 0.002657 | 0.004473 | 0.012412 | 0.008477 | 4.320051 | 0.009403 |
| 6742 | 0.50 | false | 0.001349 | 0.002472 | 0.006094 | 0.004160 | 2.121143 | 0.006481 |
| 6742 | 1.00 | false | 0.002699 | 0.004945 | 0.012189 | 0.008319 | 4.242287 | 0.012962 |

Important details:

```text
alpha=1.0:
  wrong-history gap passes, but normal first-action drift p95 fails.

alpha=0.5:
  normal first-action drift mostly passes, but gap mean and ratio fail.
```

So the blocker is not missing representation signal. The blocker is executing
the residual safely: the learned sequence separation is too front-loaded into
the first action under the current normal-drift gate.

## Classification

M674 should be classified as:

```text
first_action_drift_vs_sequence_gap_conflict
```

Secondary labels:

```text
implementation_clean
exact_gate_failure
normal_retention_failure_at_high_alpha
wrong_gap_failure_at_low_alpha
no_actor_mutation
```

This is not a PPO washout and not an actor-input contract issue.

## Interpretation

M671 proved that a frozen fused-plus-next-hidden head can create source-heldout
sequence separation. M674 shows that naively executing the first residual from
that sequence head does not yet satisfy the stricter actor-coupling gate.

The next design should make the first executed residual explicitly safe rather
than only controlling sequence-average normal residual.

Possible directions for the next design:

```text
first-step normal drift penalty / hard gate in training;
two-head structure: safe first residual + diagnostic future sequence;
separate executed-action alpha from diagnostic-sequence alpha;
target shape that moves wrong-history separation later in the sequence;
normal branch first-action anchor stronger than sequence-average anchor.
```

## Decision

```text
response_amplification_actor_coupling_exact_gate_failed_admit_audit
```

## Next

```text
m675-response-amplification-actor-coupling-audit
```
