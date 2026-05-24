# M691 Gate-Margin Closed-Loop Replay Design

## Purpose

M691 designs the no-training replay admission gate needed after the M689 exact
diagnostic pass.

Question:

```text
Does the M689 residual-head correction have trajectory-level utility when
replayed in short closed-loop continuations?
```

This milestone is design-only:

```text
no training
no PPO
no actor update
no checkpoint promotion
no actor-input change
```

## Background

M689 passed the registered exact output gates:

```text
passed_seed_count:   3 / 3
selected_alpha:      1.0
normal mean:         0.001380 - 0.001461
gap mean:            0.010731 - 0.011165
gap ratio:           3.734864 - 3.885905
first drift p95:     0.003748 - 0.004017
```

M690 audited that pass as real but diagnostic-only. The caveat is important:

```text
normal_gate_mean: about 0.436 - 0.448
wrong_gate_mean:  about 0.533 - 0.545
target margin:    0.30
observed margin:  about 0.062
```

So M689 proves output-level separation in the frozen residual head. It does not
yet prove closed-loop driving improvement.

## Design Principle

M692 should treat PPO and actor update as blocked until replay admission passes.

The safe ladder is:

```text
M691 design replay admission
  no training
  no checkpoint

M692 implement replay admission
  load M689 residual heads
  reconstruct source-heldout snapshots
  compare short closed-loop variants
  no training
  no checkpoint

later design-only actor-update branch
  only if M692 proves replay utility
```

## Replay Surface

Use the M671/M689 source-heldout rows as the first replay surface:

```text
runs/m671_response_amplification_shadow/shadow_corpus.npz
runs/m671_response_amplification_shadow/shadow_metadata.csv
runs/m689_gate_margin_response_amplification/seed_*/residual_sequence_head.pt
```

M692 should start with the selected M689 seeds:

```text
6890
6891
6892
```

and selected alpha:

```text
alpha = 1.0
```

The initial replay should be source-heldout focused because M689's exact pass
was selected on source-heldout validation rows. If source-heldout replay is
ambiguous, M692 should report train and source-heldout separately rather than
collapsing them.

## Variants

For each reconstructable row, compare at least:

```text
base_normal:
  unchanged base actor, normal recurrent hidden

residual_normal:
  first action = base actor action + alpha * residual_head(normal features)[0]
  continuation = unchanged base actor

base_wrong:
  unchanged base actor, wrong recurrent hidden

residual_wrong:
  first action = base wrong action + alpha * residual_head(wrong features)[0]
  continuation = unchanged base actor

zero_residual:
  explicitly verifies the wrapper is behavior-identical to base action
```

Optional diagnostic variants:

```text
wrong_residual_on_normal:
  execute wrong-history residual on normal hidden to test misapplied correction

normal_residual_on_wrong:
  execute normal-history residual on wrong hidden to test correction specificity
```

Only the first action should be overridden in M692. This keeps the first
closed-loop test aligned with how the deployed actor currently acts:

```text
observe -> one action -> environment transitions -> observe again
```

Sequence execution can be a later design branch if first-action replay passes.

## Implementation Reuse

M692 should reuse existing snapshot and replay utilities rather than hand-roll
environment state logic:

```text
autodrift.matched_history_outcome_gate.collect_requested_outcome_snapshots
autodrift.matched_history_outcome_gate.replay_outcome_variant
autodrift.hidden_swap_gate.action_trajectory_distances
autodrift.response_amplification_actor_coupling.GatedResponseAmplifierHead
autodrift.response_amplification_actor_coupling.evaluate_alpha_ladder
```

If the M671 shadow corpus rows cannot be reconstructed into environment
snapshots, M692 must fail as a replay-surface construction result, not silently
fall back to output-only exact metrics.

## Proposed CLI

M692 should implement a command like:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.gate_margin_replay_admission \
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

## Required Artifacts

```text
runs/m692_gate_margin_closed_loop_replay/summary.json
runs/m692_gate_margin_closed_loop_replay/replay_rows.csv
runs/m692_gate_margin_closed_loop_replay/seed_summary.csv
runs/m692_gate_margin_closed_loop_replay/split_summary.csv
docs/m692-gate-margin-closed-loop-replay-implementation.md
```

Required summary fields:

```text
rows_attempted
rows_reconstructable
rows_replayed
source_holdout_rows
residual_head_count
selected_alpha
actor_parameters_changed: false
base_actor_checkpoint_written: false
training_started: false
ppo_used: false
promoted: false

normal_first_action_l2_p95
normal_margin_regression_mean
normal_margin_regression_p95
wrong_margin_improvement_mean
wrong_risk_improvement_mean
wrong_success_improvement_count
wrong_collision_reduction_count
replay_admission_passed
```

## Replay Gates

M692 passes only if all implementation-contract gates pass:

```text
actor_parameters_changed == false
base_actor_checkpoint_written == false
training_started == false
ppo_used == false
promoted == false
rows_replayed > 0
source_holdout_rows > 0
```

and the replay behavior gates do not reject:

```text
normal_first_action_l2_p95 <= 0.006
normal_margin_regression_mean <= 0.005
normal_margin_regression_p95 <= 0.020
wrong_margin_improvement_mean >= 0.000
wrong_risk_improvement_mean >= 0.000
```

Because M689 was a diagnostic head rather than a trained actor, M692 should not
require a large improvement threshold on the first implementation. It should
classify the result into one of:

```text
replay_positive:
  wrong-history or boundary-risk improves without normal regression

replay_neutral:
  normal retention holds but wrong-history utility is near zero

normal_regression:
  residual correction harms normal replay

surface_reconstruction_failure:
  source-heldout rows cannot be replayed
```

Only `replay_positive` can admit a later actor-update design. `replay_neutral`
should trigger a branch synthesis or a return to source-diverse terminal-boundary
target mining.

## Forbidden Shortcuts

Do not:

```text
train the residual head
train the actor
run PPO
write a new actor checkpoint
promote M689
change actor observations
use hidden physical parameters as actor inputs
replace replay gates with exact output gates
hide normal-regression rows behind aggregate wrong-history improvement
```

## Decision String

```text
gate_margin_closed_loop_replay_design_admit_m692
```

## Next

```text
m692-gate-margin-closed-loop-replay-implementation
```
