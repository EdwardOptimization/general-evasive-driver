# M692 Gate-Margin Closed-Loop Replay Implementation

## Purpose

M692 implements the no-training replay admission gate designed in M691.

Question:

```text
Do the selected M689 gate-margin residual heads have short-horizon
closed-loop trajectory utility when executed as first-action corrections?
```

This milestone is implementation-only:

```text
no actor training
no residual-head training
no PPO
no base actor checkpoint
no promotion
no actor-input change
```

## Implementation

M692 adds:

```text
src/autodrift/gate_margin_replay_admission.py
tests/test_gate_margin_replay_admission.py
```

The replay tool:

```text
loads the frozen M568 base actor
loads the M671 source-heldout shadow corpus and metadata
loads the three selected M689 residual heads
reconstructs requested outcome snapshots
compares base first actions with residual-corrected first actions
rolls out short closed-loop continuations after the first-action override
writes summary, row-level, seed-level, and split-level artifacts
checks that the base actor checksum is unchanged
```

Only the first action is overridden. The continuation returns to the unchanged
base actor, matching the current deployed one-step receding control contract.

## Command

```bash
rm -rf runs/m692_gate_margin_closed_loop_replay && \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.gate_margin_replay_admission \
  --checkpoint runs/m568_scaled_l3_bc_seed5660/checkpoint.pt \
  --shadow-corpus runs/m671_response_amplification_shadow/shadow_corpus.npz \
  --metadata runs/m671_response_amplification_shadow/shadow_metadata.csv \
  --residual-head runs/m689_gate_margin_response_amplification/seed_6890/residual_sequence_head.pt \
  --residual-head runs/m689_gate_margin_response_amplification/seed_6891/residual_sequence_head.pt \
  --residual-head runs/m689_gate_margin_response_amplification/seed_6892/residual_sequence_head.pt \
  --alpha 1.0 \
  --surface-config fresh=configs/ppo_m541_matched_l3_variance_4096.json \
  --surface-config ood=configs/eval_m574_moderate_ood_l3.json \
  --max-source-heldout-rows 120 \
  --max-continuation-steps 40 \
  --max-first-action-l2 0.006 \
  --min-wrong-risk-improvement 0.01 \
  --max-normal-margin-regression 0.005 \
  --device cpu \
  --run-dir runs/m692_gate_margin_closed_loop_replay
```

## Artifacts

```text
runs/m692_gate_margin_closed_loop_replay/summary.json
runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
runs/m692_gate_margin_closed_loop_replay/seed_summary.csv
runs/m692_gate_margin_closed_loop_replay/split_summary.csv
runs/m692_gate_margin_closed_loop_replay/skipped_rows.csv
```

## Result

The implementation contract passed:

```text
rows_attempted:                 120
rows_reconstructable:           120
rows_replayed:                  360
source_holdout_rows:            120
residual_head_count:            3
selected_alpha:                 1.0
actor_parameters_changed:       false
base_actor_checkpoint_written:  false
training_started:               false
ppo_used:                       false
promoted:                       false
```

Normal-history retention held:

```text
normal_first_action_l2_p95:      0.003928
normal_margin_regression_mean:  -0.000000
normal_margin_regression_p95:    0.000008
```

Wrong-history or boundary-risk utility was near zero:

```text
wrong_margin_improvement_mean:       0.000025
wrong_risk_improvement_mean:         0.000025
wrong_success_improvement_count:     0
wrong_collision_reduction_count:     0
```

Per-head summaries were consistent:

| head seed | rows | normal first L2 p95 | normal margin regression p95 | wrong risk improvement mean | success improvements |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 6890 | 120 | 0.003858 | 0.000008 | 0.000025 | 0 |
| 6891 | 120 | 0.004017 | 0.000008 | 0.000026 | 0 |
| 6892 | 120 | 0.003748 | 0.000009 | 0.000025 | 0 |

Classification:

```text
replay_result_class:       replay_neutral
replay_admission_passed:   false
```

## Interpretation

M692 is a clean implementation pass but not a closed-loop behavior pass.

Allowed claim:

```text
The M689 residual heads can be loaded and replayed on reconstructed
source-heldout snapshots without mutating the actor, and their first-action
corrections preserve normal-history short-horizon behavior.
```

Rejected claim:

```text
The M689 exact output separation improves closed-loop wrong-history or
boundary-risk behavior enough to justify actor update, PPO, or promotion.
```

The gap is important. M689 showed exact output-level separation; M692 shows that
this output-level correction does not yet translate into meaningful
short-horizon trajectory utility on the replay surface.

## Decision

Do not:

```text
promote M689 residual heads
run actor update from this residual head
run PPO from this residual head
continue scalar residual tuning without branch synthesis
claim closed-loop self-identification improvement
```

Do:

```text
run M693 as a process synthesis and branch-decision audit
classify the result as replay_neutral / metric-artifact risk
decide whether the response-amplification actor-coupling branch should pivot
toward a trajectory/terminal-boundary objective or stop
```

## Validation

```text
python -m compileall -q src tests
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_gate_margin_replay_admission.py \
  tests/test_research_validate.py \
  tests/test_research_manifest.py \
  tests/test_research_cycle.py
```

## Decision String

```text
gate_margin_replay_neutral_admit_synthesis_audit
```

## Next

```text
m693-gate-margin-closed-loop-replay-audit
```
