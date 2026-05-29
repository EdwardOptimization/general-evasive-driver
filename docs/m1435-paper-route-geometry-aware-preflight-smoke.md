# M1435 Paper-Route Geometry-Aware Preflight Smoke

## Summary

M1435 ran the preflight-only geometry-aware selector on the public M1425 source
rows.

Decision:

```text
geometry_aware_preflight_no_forward_rows_route_to_audit
```

M1435 did not run bounded replay, outcome interventions, training, PPO,
promotion, private holdout, corpus export, or actor-input changes.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bounded_relocation_replay_probe \
  --preflight-only \
  --checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --config configs/m1419_warmup_gate_invasiveness_retune_source_wave.json \
  --candidate-rows runs/m1425_action_divergent_outcome_pressure_source_smoke/outcome_pressure_rows.csv \
  --max-candidate-rows 128 \
  --per-capability-pair-cap 12 \
  --per-seed-cap 24 \
  --per-reveal-bucket-cap 12 \
  --per-variant-cap 48 \
  --history-length 56 \
  --min-sequence-action-l2 0.025 \
  --min-source-body-x 4.0 \
  --device cpu \
  --run-dir runs/m1435_geometry_aware_preflight_smoke
```

## Result

```text
input_rows: 846
history_candidate_rows: 846
geometry_pass_rows: 0
selected_candidate_rows: 0
rejected_rows: 0
replay_started: false
training_started: false
ppo_used: false
promoted: false
actor_input_contract_changed: false
```

Rejection reasons:

```text
source_body_x_too_close|relocation_body_x_clipped: 789
source_body_x_too_close: 57
```

Source body-x diagnostics:

```text
min: -3.508074
p05: -2.971817
p25: -1.640233
p50: -0.205025
p75: 1.495281
p95: 3.812155
max: 3.908281
```

Raw relocated body-x diagnostics:

```text
min: -5.508074
p50: -1.702453
p95: 2.162954
max: 3.495281
```

Variant coverage in the preflight input:

```text
warmup_removed: 456
warmup_shortened_8: 306
delayed_warmup_history_16: 72
delayed_warmup_history_8: 12
```

## Interpretation

M1435 is a source-pool geometry failure, not a replay failure and not evidence
that history is unnecessary. The M1425 pressure rows are too late or too close:
all source obstacles fail the `source_body_x >= 4.0` gate, and most requested
relocations clip to the artificial minimum forward distance.

This supports M1430's audit more strongly: the problem is not merely M1429's
top-128 selection. The full M1425 pressure-row pool is incompatible with the
forward/unclipped geometry gate.

## Blocked Interpretations

Do not claim:

```text
preflight failure disproves history usefulness;
M1425/M1429 rows are ready for replay or training;
lowering source_body_x below 4.0 is justified by this result;
preflight rows are actual replay evidence.
```

## Next Route

Admit:

```text
m1436-paper-route-geometry-preflight-result-audit
```

The audit should decide whether to pivot to earlier-reveal/source mining, a
different source family, or stop this branch. It should not lower geometry gates
or run replay directly from M1435 rows.
