# M590 BC Hidden-Action Sensitivity Probe Design

## Purpose

M590 designs a no-oracle probe to explain the M587/M589 gap:

```text
BC5660 transfers useful route behavior,
but wrong/delayed recurrent history barely changes its action.
```

This milestone is design-only:

```text
no evaluation
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Question

The next probe must separate four different explanations:

1. The actor head structurally ignores recurrent hidden features.
2. The actor head can use hidden features, but real rollout hidden states are
   collapsed or action-equivalent.
3. The actor head responds to out-of-distribution hidden states, but the M586
   matched-current pairs are too weak.
4. The branch is simply current-frame dominant: current response and previous
   command slots explain nearly all action variation.

Only the first two are objective/architecture bottlenecks. The third points to
surface mining. The fourth means BC route success should not be interpreted as
self-ID evidence.

## Tool Plan

M591 should implement a small probe module, preferably:

```text
python -m autodrift.bc_hidden_action_sensitivity_probe
```

It can reuse helper logic from `matched_history_intervention_gate`:

- reconstruct online-GRU snapshots at requested seeds and steps;
- compute deterministic action from `(observation, hidden)`;
- zero current response and previous-command slots for positive controls;
- summarize action distances by checkpoint, surface, target, and variant.

The new tool should add:

- fusion-layer hidden/context chunk norm audit;
- hidden perturbation variants beyond M587;
- hidden-distance/action-distance correlation summaries;
- BC5660/BC5661/BC5662 family comparison.

## Inputs

Primary checkpoint family:

```text
runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
runs/m568_scaled_l3_bc_seed5661/checkpoint.pt
runs/m568_scaled_l3_bc_seed5662/checkpoint.pt
```

Primary BC5660 matched-current surfaces:

```text
runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv
runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv
```

Primary configs:

```text
configs/ppo_m541_matched_l3_variance_4096.json
configs/eval_m574_moderate_ood_l3.json
```

For BC5661/BC5662, M591 should at minimum run the weight-norm audit and route
snapshot hidden perturbation probe. Matched-current wrong-history conclusions
for those checkpoints require either their own pair mining or a clearly marked
secondary analysis; BC5660 remains the only checkpoint with existing M586
matched-current surfaces.

## Metrics

### 1. Fusion Chunk Norms

For `human_view_online_gru`, the first fusion layer consumes:

```text
[next_hidden, context_encoded, next_hidden * context_encoded]
```

M591 should compute Frobenius norms of the three chunks from
`response_context_fusion.0.weight`:

```text
hidden_chunk_norm
context_chunk_norm
interaction_chunk_norm
hidden_chunk_share = hidden / total
interaction_chunk_share = interaction / total
```

This is not proof of use, but it is a cheap structural check.

### 2. Action Sensitivity Rows

For each selected snapshot, record:

```text
checkpoint_label
surface
target
seed
step
variant
hidden_distance
action_distance
action_distance_above_threshold
normal_action
variant_action
```

Keep the M587 action threshold for continuity:

```text
min_action_distance = 0.02
```

### 3. Hidden Perturbation Variants

Required hidden variants:

| variant | observation | hidden |
| --- | --- | --- |
| normal | left/current | left/current |
| reset_hidden | left/current | initial zero hidden |
| delayed_history | left/current | left hidden from `step - delay_steps` |
| wrong_matched_history | left/current | right hidden from matched-current pair |
| shuffled_history | left/current | hidden from another row in the same surface |
| scaled_hidden_0_5 | left/current | `0.5 * left_hidden` |
| scaled_hidden_1_5 | left/current | `1.5 * left_hidden` |
| scaled_hidden_2_0 | left/current | `2.0 * left_hidden` |
| random_hidden_fit | left/current | sampled from empirical hidden mean/std |
| random_hidden_unit | left/current | standard normal scaled to empirical norm |

Required observation positive controls:

| variant | observation | hidden |
| --- | --- | --- |
| zero_current_response | response slots zeroed | left/current |
| zero_action_history | previous command slots zeroed | left/current |

The random variants are diagnostic only. They must not be interpreted as
self-ID proof, because they may leave the real rollout hidden manifold.

### 4. Correlation Summary

For each checkpoint/surface/variant, report:

```text
pair_count
hidden_distance_mean
hidden_distance_p90
action_distance_mean
action_distance_p90
above_threshold_count
above_threshold_fraction
hidden_action_distance_corr
```

The key diagnostic is whether increasing hidden perturbation magnitude produces
action movement, and whether real wrong/delayed histories lie on an
action-invariant manifold.

## Output Artifacts

M591 should write:

```text
runs/m591_bc_hidden_action_sensitivity_probe/summary.json
runs/m591_bc_hidden_action_sensitivity_probe/weight_chunk_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe/action_sensitivity_rows.csv
runs/m591_bc_hidden_action_sensitivity_probe/variant_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe/correlation_summary.csv
docs/m591-bc-hidden-action-sensitivity-probe.md
```

If M591 splits fresh and OOD into separate run directories, each directory must
have its own `summary.json`, and the milestone doc must include an aggregate
table.

## Interpretation Rules

Pre-register these outcomes:

| observed result | interpretation | next branch |
| --- | --- | --- |
| random/scaled hidden weak and hidden chunk share low | actor head effectively ignores hidden | hidden-use objective or architecture repair design |
| random/scaled hidden strong but wrong/delayed hidden weak | actor can react to hidden off-manifold, but real BC hidden states are action-equivalent or pair surface is weak | mine stronger matched-history corpus or add contrastive objective |
| wrong/delayed hidden strong on BC5660 | action-level history signal exists | persistent outcome gate can be reconsidered |
| zero-current/zero-action strong while all hidden variants weak | branch is current-frame dominant | do not claim self-ID; design hidden-use training objective |
| BC5660/5661/5662 differ materially | seed family has hidden-use variance | repeat pair mining per checkpoint before choosing a repair target |

## M591 Pass Criteria

M591 should pass as a probe if:

- all requested artifacts are written;
- all three BC seeds have weight-chunk summaries;
- BC5660 has fresh and OOD matched-current hidden-variant summaries;
- action-distance threshold and interpretation rules are unchanged from this
  design;
- P0 actor input contract is unchanged;
- no checkpoint is promoted.

M591 should fail or block if:

- the tool cannot reconstruct online-GRU snapshots for M586 rows;
- the probe silently mixes BC5660 pair labels into BC5661/BC5662 matched-current
  claims;
- random-hidden sensitivity is reported as self-ID proof;
- any actor input contract is changed.

## Decision

```text
bc_hidden_action_sensitivity_probe_design_admit_m591_probe
```

M590 passes because it specifies the exact probe metrics, variants, artifacts,
and interpretation rules needed before any hidden-use repair training.

## Next

```text
M591: implement and run the BC hidden-action sensitivity probe.
```
