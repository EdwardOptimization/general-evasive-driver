# M1365 Paper-Route Bidirectional Broader Public Replay

## Summary

M1365 ran the broader public replay and behavior diagnostic gate for the M1362
alpha `0.1` candidate.

Decision:

```text
bidirectional_broader_public_replay_pass_route_to_result_audit
```

This is a strong positive public diagnostic result. It is still not a promotion.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.public_base_controlled_fusion_candidate_replay_gate \
  --base-checkpoint runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt \
  --candidate-checkpoint runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt \
  --run-dir runs/m1365_bidirectional_broader_public_replay \
  --device cpu \
  --behavior-episodes 80
```

## Result

Summary:

```text
result_class: public_base_controlled_fusion_candidate_replay_gate_pass
six_public_replay_gates_pass: true
public_replay_gates_passed: 6 / 6
source_diverse_protected_status: pass
old_key_9944_status: diagnostic_only
behavior_pass: true
behavior_seed9505_success_delta: 0.0
behavior_seed9506_success_delta: 0.0
reset_zero_all_ordering_retained: true
actor_inputs_changed: false
ppo_used: false
promoted: false
```

Six public replay surfaces:

```text
M183/M168: pass, success_drop_count 16 -> 16, margin_gap_delta -0.0002488600
M183/M170: pass, success_drop_count 17 -> 17, margin_gap_delta -0.0002484803
M193/M189: pass, success_drop_count 14 -> 14, margin_gap_delta -0.0002369524
M212/M204: pass, success_drop_count 17 -> 17, margin_gap_delta -0.0001939721
M223/M219: pass, success_drop_count 17 -> 17, margin_gap_delta -0.0001940120
M267/M264: pass, success_drop_count 17 -> 17, margin_gap_delta -0.0001940233
```

Behavior:

```text
seed 9505: base success 0.8625, candidate success 0.8625, reset 0.85, zero_all 0.8
seed 9506: base success 0.8625, candidate success 0.8625, reset 0.85, zero_all 0.8
```

Source-diverse protected diagnostic:

```text
3 / 3 replay gates passed
```

Old-key neighborhood diagnostic:

```text
diagnostic_only
candidate accepted_cases: 25 / 40
base accepted_cases: 24 / 40
```

## Interpretation

M1365 is the first result in this branch where the M1362 alpha `0.1` candidate
survives the wider public replay stack while preserving behavior seeds. This
substantially raises the candidate from a two-surface preflight result to a broad
public diagnostic pass.

The result still should not be overclaimed:

```text
no private holdout
no fresh scenario distribution
no PPO continuation
no promotion decision
no paper-level self-identification claim
```

The correct next step is a result audit. That audit should decide whether to run
a promotion-style public gate, refresh protected surfaces, or synthesize the
branch before continuing.

## Guardrails

M1365 performs no training, PPO, actor update, private holdout, promotion,
threshold relaxation, actor-input expansion, high-fidelity claim, paper-level
claim, or closed-loop self-identification claim.

## Next

```text
m1366-paper-route-bidirectional-broader-public-replay-result-audit
```
