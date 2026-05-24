# M671 Action-Boundary Response-Amplification Shadow Implementation

## Purpose

M671 implements the frozen-actor response-amplification shadow objective
designed in M670.

This milestone is diagnostic only:

```text
no actor update
no PPO
no checkpoint promotion
```

The question is whether a small shadow head can read frozen BC5660 feature
views and create sustained wrong-history action-sequence separation on
source-heldout rows while preserving normal-history actions.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.response_amplification_shadow \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --candidate-rows runs/m667_normal_success_boundary_source_miner/candidate_scores.csv \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --views fused,next_hidden,fused_plus_next_hidden \
  --seeds 6700,6701,6702 \
  --sequence-lengths 5,7,9 \
  --max-rows 768 \
  --max-rows-per-physical-pair 18 \
  --max-rows-per-left-seed 36 \
  --target-wrong-sequence-mean-l2 0.012 \
  --max-abs-delta 0.03 \
  --target-gap 0.010 \
  --epochs 240 \
  --learning-rate 0.001 \
  --weight-decay 0.0001 \
  --hidden-dim 64 \
  --device cpu \
  --run-dir runs/m671_response_amplification_shadow
```

## Artifacts

```text
runs/m671_response_amplification_shadow/summary.json
runs/m671_response_amplification_shadow/shadow_corpus.npz
runs/m671_response_amplification_shadow/shadow_metadata.csv
runs/m671_response_amplification_shadow/seed_view_summary.csv
runs/m671_response_amplification_shadow/row_shadow_metrics.csv
runs/m671_response_amplification_shadow/split_shadow_summary.csv
```

The implementation also writes one shadow-head checkpoint per view/seed. It
does not write an actor checkpoint.

## Corpus Reconstruction

M671 reconstructs a source-heldout shadow corpus from M667 candidates:

```text
selected_candidate_rows: 648
shadow_corpus_rows:     648
source_count:           216
physical_pair_count:    100
train_rows:             528
source_holdout_rows:    120
missing_snapshot_rows:  0
rejected_direction_rows: 0
```

Weights are source-balanced:

```text
total_weight:                 1.000000
expected_source_weight:       0.004630
max_abs_source_weight_error:  0.000000
source_weight_balanced:       true
```

The corpus covers both surfaces and three targets:

```text
surfaces: fresh, ood
targets: aes_feasible, drift_required, unavoidable
```

## Shadow Gate Results

Overall:

```text
shadow_passed: true
passed_views:  fused_plus_next_hidden
actor_parameters_changed: false
actor_checkpoint_written: false
ppo_used: false
promoted: false
```

Per view/seed source-heldout metrics:

| view | seed | pass | normal mean | normal p95 | gap mean | gap p10 | gap ratio | wrong target improvement |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fused | 6700 | false | 0.003580 | 0.008194 | 0.005455 | 0.003811 | 1.898476 | 0.482956 |
| fused | 6701 | false | 0.003327 | 0.005550 | 0.007345 | 0.004688 | 2.556527 | 0.596013 |
| fused | 6702 | false | 0.003568 | 0.005847 | 0.006856 | 0.004708 | 2.386300 | 0.571876 |
| next_hidden | 6700 | false | 0.003098 | 0.004690 | 0.012323 | 0.008573 | 4.289063 | 0.860227 |
| next_hidden | 6701 | false | 0.002825 | 0.004760 | 0.012322 | 0.008647 | 4.288666 | 0.905340 |
| next_hidden | 6702 | false | 0.002742 | 0.004401 | 0.011867 | 0.008193 | 4.130226 | 0.898007 |
| fused_plus_next_hidden | 6700 | true | 0.002327 | 0.004224 | 0.012136 | 0.008244 | 4.223965 | 0.910229 |
| fused_plus_next_hidden | 6701 | false | 0.002555 | 0.004801 | 0.012398 | 0.008459 | 4.315166 | 0.897438 |
| fused_plus_next_hidden | 6702 | true | 0.002360 | 0.003834 | 0.012534 | 0.008509 | 4.362418 | 0.902770 |

The fused-plus-next-hidden view passes in `2/3` seeds, satisfying the M671
non-fused view criterion. The next-hidden view creates enough wrong-history
gap, but misses the normal-retention mean threshold. The fused view fails both
gap and normal-retention requirements.

## Interpretation

M671 is a positive frozen-shadow result:

```text
wrong-history information is usable when the shadow head sees fused features
plus next recurrent hidden state;
normal-history residuals can be kept within the pre-registered source-heldout
threshold in 2/3 seeds;
the existing fused policy boundary alone remains too weak.
```

This does not prove closed-loop self-identification, because the deployable
actor was not changed and no replay/outcome gate was run. It does show that the
current action-boundary blocker is not purely a data issue: a small trainable
head can amplify sustained wrong-history sequence separation from frozen
features without actor mutation.

## Decision

```text
response_amplification_shadow_positive_admit_audit
```

## Next

```text
m672-response-amplification-shadow-audit
```
