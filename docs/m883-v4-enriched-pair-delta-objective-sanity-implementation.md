# M883 V4 Enriched Pair-Delta Objective Sanity Implementation

## Purpose

M883 implements exact no-update sanity metrics for the M882 enriched
pair-delta objective design.

The implementation question is:

```text
Can the enriched pair-delta action targets be evaluated under reconstructed
actor observation and recurrent hidden tensors without training or PPO?
```

M883 is no-update:

```text
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_enriched_pair_delta_objective_sanity \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --residual-head runs/m761_v4_sequence_objective_probe/residual_head.pt \
  --scenario-config configs/extreme_fault_distribution_v4_low_margin_refresh_scenarios.json \
  --source-rows runs/m825_v4_extreme_hidden_dynamics_data_route/source_rows.csv \
  --objective-train-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_train_public_rows.csv \
  --objective-eval-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_objective_eval_public_rows.csv \
  --source-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_source_holdout_public_rows.csv \
  --new-signature-holdout-rows runs/m880_v4_pair_delta_objective_target_enrichment/enriched_new_signature_holdout_public_rows.csv \
  --run-dir runs/m883_v4_enriched_pair_delta_objective_sanity \
  --device cpu
```

## Implementation

M883 adds:

```text
src/autodrift/v4_enriched_pair_delta_objective_sanity.py
tests/test_v4_enriched_pair_delta_objective_sanity.py
```

The tool:

```text
1. reconstructs source snapshots from M825 source rows and the v4 low-margin
   scenario config;
2. evaluates normal_action and override_action log probabilities under the
   reconstructed normal observation and recurrent hidden state;
3. computes improvement and degradation preference losses;
4. reports metrics per split;
5. verifies actor parameters are unchanged.
```

## Result

M883 passed the registered exact-sanity gates:

```text
result_class: v4_enriched_pair_delta_objective_sanity_pass
expected_rows: 247
tensor_rows_reconstructed: 247
missing_tensor_count: 0
snapshot_rows: 19
snapshot_rejections: 0
unique_pair_requests: 43
exact_losses_finite: true
improvement_rows_present: true
degradation_rows_present: true
per_split_metrics_written: true
objective_loss_mean: 1.7962036213105181
actor_parameters_changed: false
training_started: false
optimizer_started: false
ppo_used: false
promoted: false
```

Per-split metrics:

```text
objective_train_public:
  rows: 124
  improvement_rows: 42
  degradation_rows: 82
  objective_loss_mean: 1.8847401661904555

objective_eval_public:
  rows: 22
  improvement_rows: 0
  degradation_rows: 22
  objective_loss_mean: 1.385935978455977

source_holdout_public:
  rows: 98
  improvement_rows: 36
  degradation_rows: 62
  objective_loss_mean: 1.7897557087932756

new_signature_holdout_public:
  rows: 3
  improvement_rows: 0
  degradation_rows: 3
  objective_loss_mean: 1.3559542894363403
```

## Interpretation

Supported claims:

```text
The enriched pair-delta corpus can be converted into exact no-update objective
metrics under reconstructed actor observation and recurrent hidden tensors.
Tensor reconstruction is not the current blocker.
The objective has finite improvement/degradation preference losses.
```

Unsupported claims:

```text
M883 proves that objective-only actor updates are useful.
M883 admits PPO.
M883 promotes a checkpoint.
M883 proves source-held-out new-evidence generalization.
M883 proves learned self-identification.
```

Remaining caveats:

```text
objective_eval_public and new_signature_holdout_public contain only
degradation rows, so improvement holdout evidence remains limited.
source_holdout_public still contains no new M873 rows.
78055 remains absent from new accepted pair-delta rows.
```

## Failure Taxonomy

`metric_artifact`:

```text
reduced because all rows used reconstructed observation/hidden tensors and no
row used reset hidden as a shortcut.
```

`objective_overfit`:

```text
still possible; M883 is an exact sanity result, not an update result.
```

`scenario_sampling_failure`:

```text
still present via no new source holdout and the 78055 caveat.
```

`contract_violation`:

```text
not observed.
```

`lineage_invalid`:

```text
not observed; source rows, scenario config, residual head, and checkpoint are
explicit in the command.
```

## Decision

Decision:

```text
v4_enriched_pair_delta_objective_sanity_pass
```

Next:

```text
m884-v4-pair-delta-objective-readiness-branch-synthesis
```

Because the `v4_pair_delta_objective_readiness` branch has accumulated a full
corpus-readiness arc from M875 through M883, synthesize before entering an
objective-only update/probe branch.
