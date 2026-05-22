# M177 Dual-Checkpoint Self-ID Proof Surface

M176 left two useful checkpoints:

- M168: strict full-replay checkpoint;
- M170: split-aware candidate branch with lower fixed objective and one
  documented knife-edge row67 stress loss.

M177 compares them on an action-level self-identification proof surface without
running more PPO.

This is a positive action-level gate, but not an outcome-level self-ID proof.

## Setup

Run:

```text
runs/m177_dual_checkpoint_action_proof_surface_seed9510
```

Command shape:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate \
  --checkpoint-policy m168_strict=runs/ppo_m168_stage1_from_m167_5168_seed6168/checkpoint.pt \
  --checkpoint-policy m170_split=runs/ppo_m170_row67_guarded_stage2_seed7170/checkpoint.pt \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --pairs-csv runs/m159_current_baseline_matched_current_zero_relvel_seed9510/matched_pairs.csv \
  --delay-steps 10 \
  --min-action-distance 0.02 \
  --max-pairs-per-checkpoint-target 80 \
  --pair-label-mode all \
  --device cpu
```

Artifacts:

```text
action_interventions.csv
variant_summary.csv
summary.json
```

The run evaluates `480` matched-current pairs per checkpoint and `4800`
intervention rows total.

## Aggregate Variant Results

| Checkpoint | Variant | Mean action distance | Above threshold | Fraction |
| --- | --- | ---: | ---: | ---: |
| m168_strict | delayed_history | 0.149858 | 452 / 480 | 0.941667 |
| m170_split | delayed_history | 0.149845 | 452 / 480 | 0.941667 |
| m168_strict | reset_hidden | 0.891897 | 456 / 480 | 0.950000 |
| m170_split | reset_hidden | 0.891607 | 456 / 480 | 0.950000 |
| m168_strict | wrong_matched_history | 0.042321 | 325 / 480 | 0.677083 |
| m170_split | wrong_matched_history | 0.043020 | 333 / 480 | 0.693750 |
| m168_strict | zero_action_history | 0.052358 | 408 / 480 | 0.850000 |
| m170_split | zero_action_history | 0.052594 | 408 / 480 | 0.850000 |
| m168_strict | zero_current_response | 0.140353 | 480 / 480 | 1.000000 |
| m170_split | zero_current_response | 0.141274 | 480 / 480 | 1.000000 |

M170 is slightly stronger on wrong-history and zero-current action sensitivity.
The only above-threshold count improvement is wrong-history: `333` versus `325`.

## Pairwise Differences

`m170_split - m168_strict` action-distance differences across the same pairs:

| Variant | Mean delta | M170 greater count |
| --- | ---: | ---: |
| wrong_matched_history | +0.000698 | 325 / 480 |
| reset_hidden | -0.000290 | 270 / 480 |
| zero_current_response | +0.000921 | 366 / 480 |
| zero_action_history | +0.000236 | 390 / 480 |
| delayed_history | -0.000013 | 256 / 480 |

The difference is real but small. It does not justify replacing the strict
checkpoint by itself.

## Interpretation

What the action-level gate supports:

- both checkpoints use response/history channels in a measurable way;
- zero-current response and reset-hidden interventions strongly alter actions;
- M170 has a small wrong-history action-sensitivity lift over M168.

What it does not prove:

- it does not prove outcome-level self-identification;
- it does not resolve the row67 strict full-replay loss;
- it does not show no-action history is behavior-critical.

## Decision

Use a dual-checkpoint protocol for the next self-ID evidence step:

- M168 remains the strict full-replay checkpoint and outcome-retention anchor;
- M170 remains the split-aware candidate with slightly stronger action-level
  history sensitivity;
- do not choose one solely by fixed objective, aggregate behavior, or action
  sensitivity.

The next step should run an outcome-level dual-checkpoint proof-surface gate
rather than more PPO.

## Validation

Evidence:

```text
runs/m177_dual_checkpoint_action_proof_surface_seed9510/summary.json
runs/m177_dual_checkpoint_action_proof_surface_seed9510/variant_summary.csv
runs/m177_dual_checkpoint_action_proof_surface_seed9510/action_interventions.csv
```
