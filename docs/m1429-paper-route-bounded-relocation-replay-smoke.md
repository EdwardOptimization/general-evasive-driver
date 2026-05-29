# M1429 Paper-Route Bounded Relocation Replay Smoke

## Summary

M1429 ran the no-training bounded relocation replay probe:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 12 \
  --history-length 56 \
  --recent-window-length 4 \
  --max-continuation-steps 48 \
  --device cpu \
  --run-dir runs/m1429_bounded_relocation_replay_smoke
```

Decision:

```text
bounded_relocation_replay_no_history_positive_route_to_geometry_audit
```

M1429 does not train, run PPO, promote, use private holdout, export a training
corpus, or change actor inputs.

## Result

```text
result_class: bounded_relocation_replay_no_history_positive
selected_candidate_rows: 128
actual_replay_rows: 384
history_positive_rows: 0
control_positive_rows: 0
normal_failed_rows: 177
rejected_rows: 0
```

Replay executed successfully and the tool did not mutate the actor:

```text
replay_started: true
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_parameters_changed: false
actor_input_contract_changed: false
```

## Diversity

```text
selected_candidate_rows: 128
selected unique_source_seeds: 3
selected unique_capability_pairs: 13
selected unique_reveal_buckets: 9
selected unique_variants: 1
selected max_single_seed_share: 0.75
```

The candidate set is not well balanced: one seed contributes 75% of selected
rows, and all selected rows use `warmup_removed`.

## Replay Variants

```text
warmup_removed rows: 128
reset_hidden rows: 128
zero_current_response rows: 128
warmup_removed history_positive_rows: 0
reset_hidden control_positive_rows: 0
zero_current_response control_positive_rows: 0
```

This is a clean negative for the selected source set: neither history nor
controls produce accepted outcome-critical rows.

## Geometry Diagnostic

M1429 exposes a source-geometry problem:

```text
normal_success selected groups: 69 true / 59 false
normal_success rows: 207 / 384
source_body_x median: -1.678050
source_body_x min: -2.971817
source_body_x max: 3.865466
relocated_body_x == 2.0 for 126 / 128 selected groups
```

Most selected rows had the source obstacle behind the vehicle at the replay
snapshot, so the replay tool clipped relocation to the minimum forward distance
of `2.0m`. That makes M1429 a valid tool exercise but a poor source selection
test.

## Interpretation

M1429 shows:

```text
bounded relocation replay tool runs;
actual replay rows are produced;
history-positive rows are zero;
source selection is geometry-poor and seed-concentrated.
```

The right next step is not training, not threshold lowering, and not another
large replay sweep. The next step is a geometry/source audit.

## Guardrails

No forbidden shortcut occurred:

```text
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
```

## Next

Next milestone:

```text
m1430-paper-route-bounded-relocation-replay-result-audit
```

M1430 should classify whether the negative is a true no-history result or a
source geometry/selection failure. It should decide whether to repair the
selector with forward-obstacle geometry preflight or synthesize/stop this
branch.
