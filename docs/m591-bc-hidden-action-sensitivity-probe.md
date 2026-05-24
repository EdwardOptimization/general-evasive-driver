# M591 BC Hidden-Action Sensitivity Probe

## Purpose

M591 implements and runs the hidden-action sensitivity probe designed in M590.
It tests whether the scaled L3 BC actor uses its online-GRU hidden state in a
way that can explain action choices on matched-current surfaces.

This milestone is diagnostic only:

```text
no training
no PPO
no behavior cloning
no checkpoint promotion
```

## Implementation

M591 adds:

```text
src/autodrift/bc_hidden_action_sensitivity_probe.py
tests/test_bc_hidden_action_sensitivity_probe.py
```

The probe writes:

```text
summary.json
weight_chunk_summary.csv
action_sensitivity_rows.csv
variant_summary.csv
correlation_summary.csv
```

It reuses the existing matched-history reconstruction path, then adds:

- fusion weight chunk norms for `hidden`, `context`, and `hidden * context`;
- delayed, wrong, shuffled, scaled, and random hidden variants;
- zero-current and zero-action observation positive controls;
- hidden-distance/action-distance correlations.

BC5660 is the only checkpoint with action rows from the existing M586 matched
surfaces. BC5661 and BC5662 are included in weight summaries only. This avoids
claiming matched-current wrong-history evidence for checkpoints whose own pair
surfaces were not mined.

## Commands

Fresh route:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_hidden_action_sensitivity_probe \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy bc5661=runs/m568_scaled_l3_bc_seed5661/checkpoint.pt \
  --checkpoint-policy bc5662=runs/m568_scaled_l3_bc_seed5662/checkpoint.pt \
  --env-config configs/ppo_m541_matched_l3_variance_4096.json \
  --pairs-csv runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv \
  --surface fresh \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-target 120 \
  --device cpu \
  --run-dir runs/m591_bc_hidden_action_sensitivity_probe_fresh
```

Moderate-OOD:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_hidden_action_sensitivity_probe \
  --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --checkpoint-policy bc5661=runs/m568_scaled_l3_bc_seed5661/checkpoint.pt \
  --checkpoint-policy bc5662=runs/m568_scaled_l3_bc_seed5662/checkpoint.pt \
  --env-config configs/eval_m574_moderate_ood_l3.json \
  --pairs-csv runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv \
  --surface ood \
  --delay-steps 2 \
  --min-action-distance 0.02 \
  --max-pairs-per-target 120 \
  --device cpu \
  --run-dir runs/m591_bc_hidden_action_sensitivity_probe_ood
```

## Artifacts

Fresh route:

```text
runs/m591_bc_hidden_action_sensitivity_probe_fresh/summary.json
runs/m591_bc_hidden_action_sensitivity_probe_fresh/weight_chunk_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe_fresh/action_sensitivity_rows.csv
runs/m591_bc_hidden_action_sensitivity_probe_fresh/variant_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe_fresh/correlation_summary.csv
```

Moderate-OOD:

```text
runs/m591_bc_hidden_action_sensitivity_probe_ood/summary.json
runs/m591_bc_hidden_action_sensitivity_probe_ood/weight_chunk_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe_ood/action_sensitivity_rows.csv
runs/m591_bc_hidden_action_sensitivity_probe_ood/variant_summary.csv
runs/m591_bc_hidden_action_sensitivity_probe_ood/correlation_summary.csv
```

## Run Summary

| surface | input pairs | action rows | variant summaries | weight summaries | skipped action labels |
| --- | ---: | ---: | ---: | ---: | --- |
| fresh | 329 | 3619 | 33 | 3 | BC5661, BC5662 |
| OOD | 287 | 3157 | 33 | 3 | BC5661, BC5662 |

## Fusion Weight Chunks

The three BC seeds have non-trivial hidden and interaction chunk norms:

| checkpoint | hidden share | context share | interaction share |
| --- | ---: | ---: | ---: |
| BC5660 | 0.321651 | 0.318387 | 0.359962 |
| BC5661 | 0.322598 | 0.320333 | 0.357069 |
| BC5662 | 0.314369 | 0.316522 | 0.369109 |

This rejects the simplest explanation:

```text
the actor architecture/head has no hidden path
```

The path exists and the trained fusion layer does not obviously zero it out.

## Fresh Route Aggregate

| variant | pairs | mean action distance | p90 action distance | above threshold | mean hidden distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| wrong_matched_history | 329 | 0.000552 | 0.001046 | 0 | 0.053664 |
| delayed_history | 329 | 0.001658 | 0.002618 | 0 | 0.064598 |
| shuffled_history | 329 | 0.003219 | 0.012284 | 15 | 0.144624 |
| scaled_hidden_0_5 | 329 | 0.007313 | 0.009312 | 0 | 0.278071 |
| scaled_hidden_1_5 | 329 | 0.006623 | 0.008435 | 0 | 0.278071 |
| scaled_hidden_2_0 | 329 | 0.012920 | 0.016451 | 0 | 0.556141 |
| random_hidden_fit | 329 | 0.005973 | 0.010556 | 0 | 0.350674 |
| random_hidden_unit | 329 | 0.018229 | 0.027147 | 127 | 0.832126 |
| reset_hidden | 329 | 0.015801 | 0.020241 | 119 | 0.556141 |
| zero_action_history | 329 | 0.018689 | 0.026798 | 189 | 0.000000 |
| zero_current_response | 329 | 0.066799 | 0.076165 | 329 | 0.000000 |

## Moderate-OOD Aggregate

| variant | pairs | mean action distance | p90 action distance | above threshold | mean hidden distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| wrong_matched_history | 287 | 0.000764 | 0.001320 | 0 | 0.065121 |
| delayed_history | 287 | 0.001218 | 0.005234 | 0 | 0.055847 |
| shuffled_history | 287 | 0.002686 | 0.007969 | 1 | 0.129866 |
| scaled_hidden_0_5 | 287 | 0.006822 | 0.009045 | 0 | 0.271400 |
| scaled_hidden_1_5 | 287 | 0.006101 | 0.008019 | 0 | 0.271400 |
| scaled_hidden_2_0 | 287 | 0.011899 | 0.015656 | 0 | 0.542801 |
| random_hidden_fit | 287 | 0.006732 | 0.011045 | 0 | 0.395982 |
| random_hidden_unit | 287 | 0.017486 | 0.026994 | 98 | 0.828531 |
| reset_hidden | 287 | 0.014932 | 0.020022 | 70 | 0.542801 |
| zero_action_history | 287 | 0.018867 | 0.025986 | 166 | 0.000000 |
| zero_current_response | 287 | 0.070125 | 0.078047 | 287 | 0.000000 |

## Interpretation

M591 supports this:

```text
BC5660 action is strongly sensitive to current response and moderately
sensitive to previous-command slots.
```

It does not support this:

```text
BC5660 action meaningfully depends on real accumulated wrong/delayed recurrent
history on the M586 matched-current surfaces.
```

The hidden path is not absent. The fusion layer gives hidden and interaction
chunks roughly one third of the first-layer norm. But real wrong/delayed hidden
states produce tiny action distances:

```text
fresh wrong/delayed means: 0.000552 / 0.001658
OOD wrong/delayed means:   0.000764 / 0.001218
```

Even scaled hidden variants stay below the `0.02` action threshold in mean and
above-threshold count. `random_hidden_unit` produces some above-threshold rows,
but it is an off-manifold diagnostic and cannot be used as self-ID proof.

The best classification is:

```text
real BC hidden states are action-equivalent on these surfaces, and the branch
is current-frame dominant.
```

This is consistent with M589: one-step teacher-action BC is not enough to force
hidden state to encode capability or causal command-response history.

## Rejected Branches

Do not run a persistent outcome gate from this branch yet.

Reason:

```text
wrong/delayed hidden action sensitivity is still absent after a sharper probe
```

Do not claim self-ID from `random_hidden_unit`.

Reason:

```text
random hidden states may leave the real rollout hidden manifold
```

Do not promote or PPO-continue BC5660 from this evidence.

Reason:

```text
the mechanistic hidden-history proof is still negative
```

## Next Branch

M592 should design a hidden-use repair objective or corpus, not a larger route
eval.

The likely repair target is:

```text
make hidden state predict or rank future response/capability on matched-current
history pairs, then only later test whether action uses that hidden state.
```

Candidate objective families:

- future response-envelope auxiliary loss;
- matched-current capability ranking loss;
- hidden contrastive loss between capability-different histories;
- teacher-action or outcome-preference loss only on rows where capability
  differences imply action differences.

## Decision

```text
bc_hidden_action_sensitivity_probe_negative_admit_hidden_use_objective_design
```

M591 passes as a diagnostic because it implements the pre-registered probe,
writes the required artifacts, preserves P0 inputs, and classifies the hidden
use bottleneck without training or promotion.

## Next

```text
M592: design the BC hidden-use repair objective or corpus.
```
