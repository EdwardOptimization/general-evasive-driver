# M757 V4 Sequence Objective Design

## Purpose

M757 designs a constrained objective branch from the M755 v4 sequence-outcome
corpus.

The question is:

```text
Can we define an objective that preserves normal-history behavior while
maintaining outcome-critical command-response sensitivity, without assuming
complete hard-negative contrast rows?
```

This milestone is design-only:

```text
no actor training
no objective update
no PPO
no checkpoint loading
no checkpoint promotion
no actor-input change
```

## Evidence Inputs

M757 uses the M755 corpus as an index and evidence corpus:

```text
runs/m755_v4_sequence_outcome_corpus_export/summary.json
runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv
runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv
runs/m755_v4_sequence_outcome_corpus_export/hard_negative_rows.csv
```

M755 corpus status:

```text
positive_rows: 1213
normal_rows: 1213
hard_negative_rows: 1009
positives_without_hard_negative: 338
unique_positive_seeds: 27
unique_positive_fault_family_pairs: 17
positive_corpus_gate_pass: true
v4_metadata_gate_pass: true
claim_boundary_level: current_model_or_proxy
```

The corpus is not a tensor dataset. It preserves row identities, source/fault
metadata, first actions, outcome gaps, and claim boundaries, but not full
training-time observations and recurrent hidden tensors.

Therefore M758 must reconstruct objective samples by replaying the original
source rows:

```text
seed
preferred_fault
step
source_index
variant
horizon
```

The M755 CSVs are the label/index layer; the replayed snapshots are the tensor
layer.

## Objective Roles

Each positive contrast group has:

```text
normal:
  matched normal-history rollout row;
  required for every positive;
  preferred behavior anchor.

positive_intervention:
  sequence_outcome_critical intervention row;
  corrupted command-response/history condition that worsens terminal outcome;
  used as outcome-sensitive rejected/intervened branch.

hard_negative_action_only:
  optional same-source/same-horizon action-critical but outcome-safe row;
  useful for separating action-only artifacts from outcome-critical evidence;
  not present for every positive.
```

The objective must not assume a hard negative exists for every positive.

## Proposed Objective

M758 should implement an exact/offline objective evaluator first, not a training
update.

For each reconstructed group `g`:

```text
a_n = current actor first action under normal history
a_i = current actor first action under the outcome-critical intervention history
m_i = terminal margin gap from normal in the M755 row
w_i = clipped outcome weight from m_i, horizon, and variant
```

The proposed design has four terms:

### 1. Normal Behavior Retention

Keep the normal-history branch close to its current behavior:

```text
L_normal = ||pi_theta(o_n, h_n) - a_n_base||^2
```

This is required for every positive group.

Purpose:

```text
do not turn diagnostic evidence into behavior regression;
protect first-step steering/throttle/brake behavior on normal histories.
```

### 2. Intervention Branch Anchor

Keep the corrupted-history branch reconstructable enough for proof gates:

```text
L_intervention_anchor = ||pi_theta(o_i, h_i) - a_i_base||^2
```

This is not a safety target. It is a proof-retention anchor for counterfactual
history interventions. It should be lower weight than `L_normal`.

Purpose:

```text
avoid collapsing corrupted-history behavior onto normal-history behavior;
preserve the diagnostic branch used to prove history dependence.
```

### 3. Outcome-Weighted Gap Preservation

Preserve or mildly amplify the normal-vs-intervention first-action gap:

```text
gap_i = ||pi_theta(o_n, h_n) - pi_theta(o_i, h_i)||_2
target_gap_i = clamp(prefix_l2_mean_base, min=0.02, max=0.06)
L_gap = w_i * relu(target_gap_i - gap_i)^2
```

Weights:

```text
w_i increases with margin_gap_from_normal;
w_i increases with horizon only up to a cap;
zero_command_obs and reset_hidden_each_step are reported separately;
claim_boundary_level is logging/stratification only, not actor input.
```

Purpose:

```text
make the objective explicitly protect the command-response sensitivity that
caused terminal outcome changes.
```

### 4. Optional Hard-Negative Calibration

If a hard-negative action-only row exists for a group, use it only as a
calibration term:

```text
L_hard_negative =
  relu(action_only_gap - outcome_gap + margin)^2
```

Interpretation:

```text
outcome-critical rows should be weighted more strongly than action-only rows;
action-only rows should not become proof positives;
missing hard negatives must not remove the positive group from training/eval.
```

Hard negatives are optional:

```text
missing_hard_negative => skip L_hard_negative for that group
```

## Total Loss For Offline Sanity

M758 should report exact full-corpus metrics for:

```text
L_total =
  lambda_normal * L_normal
+ lambda_intervention_anchor * L_intervention_anchor
+ lambda_gap * L_gap
+ lambda_hard_negative * L_hard_negative_optional
```

Initial coefficients for sanity only:

```text
lambda_normal: 1.0
lambda_intervention_anchor: 0.25
lambda_gap: 0.50
lambda_hard_negative: 0.10
```

M758 should not update actor parameters. It should only reconstruct samples,
compute exact losses on the current base checkpoint, and report whether the
objective is well-formed and source-balanced.

## Exact Metrics

M758 should write metrics by:

```text
overall
variant
horizon
seed
preferred_fault_family
wrong_fault_family
fault_family_pair
source_pool
claim_boundary_level
hard_negative_available
```

Required metrics:

```text
sample_count
positive_group_count
normal_anchor_mse_mean
intervention_anchor_mse_mean
normal_intervention_gap_mean
normal_intervention_gap_p10
target_gap_mean
gap_deficit_mean
gap_deficit_p95
hard_negative_available_fraction
hard_negative_calibration_loss_mean
first_action_drift_from_base_mean
first_action_drift_from_base_p95
```

The exact evaluator should also report reconstruction failures:

```text
missing_source_snapshot
missing_normal_replay
missing_intervention_replay
normal_history_failed
duplicate_group_id
metadata_missing
```

## Gates For M758

M758 should pass only if:

```text
sample_reconstruction_success_rate >= 0.98
metadata_missing_rows == 0
normal_group_count == positive_rows
hard_negative_missing_rows are counted but not fatal
normal_anchor_mse_mean is finite
intervention_anchor_mse_mean is finite
normal_intervention_gap_mean >= 0.02
gap_deficit_mean is finite
claim_boundary_levels == [current_model_or_proxy]
training_started == false
checkpoint_loaded_for_eval_only == true
optimizer_started == false
ppo_used == false
promoted == false
```

M758 should classify results as:

```text
v4_sequence_objective_sanity_pass:
  reconstruction and exact metrics pass

v4_sequence_objective_hard_negative_sparse:
  reconstruction passes but hard-negative availability remains sparse

v4_sequence_objective_reconstruction_blocked:
  source snapshots or intervention replays cannot be reconstructed

v4_sequence_objective_metadata_artifact:
  v4 claim-boundary or source metadata is missing

v4_sequence_objective_degenerate:
  exact gap or loss metrics are non-finite or near-zero
```

## Forbidden Shortcuts

M758 must not:

```text
train actor parameters;
run PPO;
promote a checkpoint;
use hidden fault labels as actor inputs;
drop matched normal rows;
discard positives without hard negatives;
treat action-only hard negatives as outcome positives;
claim true four-wheel/single-wheel physics.
```

## Registered M758 Shape

M758 should implement a module with a command shape similar to:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.v4_sequence_objective_sanity \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --corpus-summary runs/m755_v4_sequence_outcome_corpus_export/summary.json \
  --positive-rows runs/m755_v4_sequence_outcome_corpus_export/positive_sequence_outcomes.csv \
  --contrast-rows runs/m755_v4_sequence_outcome_corpus_export/contrast_rows.csv \
  --fault-config configs/extreme_fault_distribution_v4_scenarios.json \
  --scenario-config configs/extreme_fault_distribution_v4_scenarios.json \
  --run-dir runs/m758_v4_sequence_objective_sanity \
  --device cpu
```

Exact implementation details may reuse M752 replay utilities, but the output
must keep M758 as an evaluator/sanity gate, not a training step.

## Next Step

M758 should implement the exact/offline objective sanity evaluator and run it on
the M755 corpus. M759 should audit the sanity output before any actor update.
