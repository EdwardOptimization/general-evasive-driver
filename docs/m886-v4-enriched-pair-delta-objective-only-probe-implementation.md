# M886 V4 Enriched Pair-Delta Objective-Only Probe Implementation

## Purpose

M886 implements the tiny no-PPO objective-only probe designed in M885.

The question was:

```text
Can the enriched pair-delta exact objective produce a small actor-coupling
direction that improves train objective rows without regressing exact public
holdouts?
```

This milestone is not a replay gate, PPO run, promotion path, or learned-driver
claim.

## Implementation

Added:

```text
src/autodrift/v4_enriched_pair_delta_objective_only_probe.py
tests/test_v4_enriched_pair_delta_objective_only_probe.py
```

The probe:

- reconstructs actor observations and recurrent hidden tensors from the M880
  enriched split rows using the same source/scenario/residual inputs as M883;
- loads `runs/m568_scaled_l3_bc_seed5660/checkpoint.pt` as base;
- loads `runs/m761_v4_sequence_objective_probe/residual_head.pt` frozen for
  reconstruction only;
- trains only `actor_coupling` parameters for 32 Adam steps;
- keeps PPO, residual-head training, actor input changes, and promotion blocked;
- writes raw and interpolated candidate metrics.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_enriched_pair_delta_objective_only_probe \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --objective-train-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv \
  --objective-eval-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv \
  --source-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv \
  --new-signature-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv \
  --run-dir runs/m886_v4_enriched_pair_delta_objective_only_probe \
  --device cpu \
  --steps 32 \
  --learning-rate 0.000001 \
  --batch-size 32 \
  --action-anchor-coef 0.1 \
  --parameter-anchor-coef 0.0001 \
  --exact-holdout-regression-tolerance 0.0001
```

## Results

Run:

```text
runs/m886_v4_enriched_pair_delta_objective_only_probe
```

Key outputs:

```text
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
raw_train_weighted_loss_delta: -0.0008391377425962521
exact_admissible_alpha_count: 7
best_exact_admissible_alpha: 0.1
best_exact_admissible_train_delta: -0.00008386037042074079
exact_losses_finite: true
training_nonfinite: false
actor_input_contract_changed: false
residual_head_changed: false
ppo_used: false
promoted: false
result_class: v4_enriched_pair_delta_objective_only_probe_exact_admissible
```

The raw candidate improved the train objective, but M885 forbids accepting raw
directly. Exact-admissible status is therefore assigned only to nonzero
interpolation candidates.

Interpolation metrics:

```text
alpha    train_delta          max_holdout_regression   exact_admissible
0.001    -0.0000008488855054  -0.0000003576278687      true
0.0025   -0.0000021385569726  -0.0000007947285969      true
0.005    -0.0000041934751696  -0.0000016291936238      true
0.01     -0.0000084258856312  -0.0000033775965373      true
0.02     -0.0000167767847739  -0.0000068744023640      true
0.05     -0.0000419909915617  -0.0000173250834148      true
0.10     -0.0000838603704207  -0.0000345706939697      true
```

Action drift stayed small:

```text
raw_candidate all action_l2_mean: 0.0011987320806356033
alpha 0.10 all action_l2_mean: 0.00011984185470731906
```

## Interpretation

M886 gives a first positive objective-only signal:

```text
The enriched pair-delta objective can produce a small actor-coupling direction
that improves exact train rows and also improves, rather than regresses, the
registered public exact holdout splits under the tested interpolation grid.
```

The result is still narrow:

- it is an exact objective result, not closed-loop replay evidence;
- all exact rows are public workflow artifacts, so overfit risk remains;
- eval and new-signature holdouts are degradation-only, so direction balance is
  still imperfect;
- no checkpoint is promoted;
- no PPO continuation is admitted yet.

## Decision

Decision:

```text
v4_enriched_pair_delta_objective_only_probe_exact_admissible
```

Next:

```text
m887-v4-enriched-pair-delta-objective-only-probe-audit
```

M887 should audit whether `alpha_0_1.pt` or a smaller admissible interpolation
candidate deserves replay/proof gate evaluation. It must not skip directly to
promotion or PPO.
