# M601 BC Capability Belief-Intervention Probe

## Purpose

M601 implements and runs the M600 capability-belief intervention probe.

Question:

```text
Does the M598 capability head move under real recurrent-history interventions
even though M591 found weak action-level movement?
```

Scope:

```text
no actor training
no capability-head training
no PPO
no route evaluation
no checkpoint promotion
```

## Implementation

Added:

```text
src/autodrift/bc_capability_belief_intervention_probe.py
tests/test_bc_capability_belief_intervention_probe.py
```

The probe loads:

```text
actor:           runs/m568_scaled_l3_bc_seed5660/checkpoint.pt
capability head: runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt
target stats:    runs/m598_bc_capability_repair_head_only_smoke/summary.json
```

For each M586 matched-current pair it reconstructs the same recurrent
snapshots as M591, applies the M600 hidden/observation variants, runs the
actor recurrent update, and evaluates the training-only capability head on
`next_hidden`:

```text
features, next_hidden = actor.recurrent_features_tensor(obs_variant, hidden_variant)
capability = capability_head(next_hidden)
```

Capability movement is measured in M598 target z-score space:

```text
capability_z_distance = ||(cap_variant - cap_normal) / target_std||_2
threshold = 0.25
```

Capability labels remain training/evaluation targets only. They do not enter
the actor input. The run does not modify actor or head weights.

## Commands

Fresh:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_belief_intervention_probe --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt --capability-head runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt --capability-summary runs/m598_bc_capability_repair_head_only_smoke/summary.json --env-config configs/ppo_m541_matched_l3_variance_4096.json --pairs-csv runs/m586_bc5660_matched_current_fresh_seed25560/matched_pairs.csv --surface fresh --delay-steps 2 --min-capability-z-distance 0.25 --max-pairs-per-target 120 --device cpu --run-dir runs/m601_bc_capability_belief_intervention_fresh
```

OOD:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.bc_capability_belief_intervention_probe --checkpoint-policy bc5660=runs/m568_scaled_l3_bc_seed5660/checkpoint.pt --capability-head runs/m598_bc_capability_repair_head_only_smoke/capability_head.pt --capability-summary runs/m598_bc_capability_repair_head_only_smoke/summary.json --env-config configs/eval_m574_moderate_ood_l3.json --pairs-csv runs/m586_bc5660_matched_current_ood_seed25660/matched_pairs.csv --surface ood --delay-steps 2 --min-capability-z-distance 0.25 --max-pairs-per-target 120 --device cpu --run-dir runs/m601_bc_capability_belief_intervention_ood
```

## Results

Fresh surface:

```text
input pairs: 329
capability rows: 3948
admission: true by shuffled_history
```

| Variant | Kind | Mean z-distance | P90 | Above threshold |
| --- | --- | ---: | ---: | ---: |
| `zero_current_response` | observation control | `1.086501` | `1.429596` | `322 / 329` |
| `reset_hidden` | reset ablation | `0.777646` | `1.079480` | `271 / 329` |
| `zero_action_history` | observation control | `0.520996` | `0.750341` | `271 / 329` |
| `shuffled_history` | real history | `0.226604` | `0.848551` | `99 / 329` |
| `wrong_matched_history` | real history | `0.099081` | `0.189764` | `8 / 329` |
| `delayed_history` | real history | `0.077070` | `0.145870` | `24 / 329` |

OOD surface:

```text
input pairs: 287
capability rows: 3444
admission: true by shuffled_history and wrong_matched_history
```

| Variant | Kind | Mean z-distance | P90 | Above threshold |
| --- | --- | ---: | ---: | ---: |
| `zero_current_response` | observation control | `1.462632` | `1.938969` | `272 / 287` |
| `reset_hidden` | reset ablation | `0.802511` | `1.275555` | `215 / 287` |
| `zero_action_history` | observation control | `0.461509` | `0.744327` | `215 / 287` |
| `shuffled_history` | real history | `0.213130` | `0.758586` | `78 / 287` |
| `wrong_matched_history` | real history | `0.140707` | `0.269658` | `49 / 287` |
| `delayed_history` | real history | `0.075159` | `0.167978` | `20 / 287` |

Random-hidden movement is strong, especially `random_hidden_unit`, but it is
off-manifold diagnostic only and is not counted as self-ID evidence.

## Interpretation

M601 passes as a process/probe milestone.

Supported:

```text
The frozen BC5660 recurrent hidden state contains capability information that
the M598 head can read, and real history substitutions can move that predicted
capability belief.
```

Important limitations:

```text
M601 still does not prove driver improvement.
M601 still does not prove action use.
M601 still does not admit PPO.
M601 does not promote any checkpoint.
```

The result is mixed rather than uniformly strong:

- `shuffled_history` passes the M600 admission rule on both surfaces.
- `wrong_matched_history` passes on OOD but is just below the mean threshold on
  fresh and has only `8 / 329` above-threshold fresh rows.
- `delayed_history` remains weak on both surfaces.
- `zero_current_response` remains the dominant positive control, so current
  response still explains much of the learned capability prediction.

This is enough to admit an audit for actor/fusion coupling design, but not
enough to start actor training directly.

## Decision

```text
bc_capability_belief_intervention_probe_pass_admit_audit
```

## Next

```text
M602: audit M601 and decide whether to design a guarded actor/fusion coupling
fine-tune, strengthen pair surfaces, or run a history-length observability
audit before any actor update.
```
