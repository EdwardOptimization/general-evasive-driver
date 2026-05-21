# M99 M98 Behavior Retention Gate

M99 checks whether the first strict objective-only hidden-envelope pass also
preserves actual driving behavior and produces any behavior-level dependence on
response history.

M98 passed the objective-only gate:

```text
braking, lateral, and yaw future-envelope after-lift > 0
across three larger-batch repeated seeds
```

But M98 only trained the response encoder, GRU, and a temporary envelope head.
The actor head was frozen during objective optimization, so behavior still needs
a separate gate.

## Loader Fix

The first M99 benchmark attempt exposed a real artifact bug:

```text
torch.load(weights_only=True) could not load M98 optimized checkpoints
because hidden_envelope_optimize saved pathlib.Path objects in metadata.
```

Fix:

```text
hidden_envelope_optimize.save_checkpoint_like now applies to_jsonable(metadata)
before torch.save.
```

Focused coverage:

```text
tests/test_hidden_envelope_optimize.py
```

After the fix, the M98 run directories were regenerated with the same commands
and the optimized checkpoints loaded through the standard
`load_actor_critic_checkpoint` path.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src conda run -n autodrift python -m autodrift.benchmark \
  --env-config configs/ppo_m24_human_view_gru_driver.json \
  --episodes 80 \
  --seed 9500 \
  --policies heuristic \
  --checkpoint-policy m62_a250=runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt \
  --checkpoint-policy m98_9480=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt \
  --checkpoint-policy m98_9481=runs/m98_larger_batch_per_target_seed9481/optimized_checkpoint.pt \
  --checkpoint-policy m98_9482=runs/m98_larger_batch_per_target_seed9482/optimized_checkpoint.pt \
  --checkpoint-policy m98_9480_reset=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt@reset_recurrent_state \
  --checkpoint-policy m98_9480_zero_current=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt@zero_current_response \
  --checkpoint-policy m98_9480_zero_all=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt@zero_all_response \
  --checkpoint-policy m98_9480_noact=runs/m98_larger_batch_per_target_seed9480/optimized_checkpoint.pt@zero_action_history \
  --device cpu \
  --run-dir runs/m99_m98_behavior_retention_gate_seed9500
```

Artifacts:

```text
runs/m99_m98_behavior_retention_gate_seed9500/policy_summary.csv
runs/m99_m98_behavior_retention_gate_seed9500/episodes.csv
```

## Results

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| heuristic | 0.2250 | 0.7750 | 37.659345 | 0.099179 | -0.309701 |
| m62_a250 | 0.8625 | 0.1375 | 64.154043 | 1.852887 | -0.106535 |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m98_9481 | 0.8750 | 0.1250 | 65.878881 | 1.866000 | -0.077736 |
| m98_9482 | 0.8750 | 0.1250 | 65.574310 | 1.848101 | -0.073838 |

Seed9480 ablations:

| policy | success | termination | return mean | clearance margin mean | clearance margin min |
| --- | ---: | ---: | ---: | ---: | ---: |
| m98_9480 | 0.8625 | 0.1375 | 65.524351 | 1.853319 | -0.115454 |
| m98_9480_noact | 0.8625 | 0.1375 | 64.867827 | 1.860228 | -0.115142 |
| m98_9480_reset | 0.8750 | 0.1250 | 65.870069 | 1.848363 | -0.080817 |
| m98_9480_zero_current | 0.8750 | 0.1250 | 65.710477 | 1.850524 | -0.157527 |
| m98_9480_zero_all | 0.8750 | 0.1250 | 65.710477 | 1.850524 | -0.157527 |

## Interpretation

M99 is mixed:

- Behavior retention passes: all three M98 objective checkpoints match or exceed
  M62 success on the shared 80-seed benchmark.
- Clearance margin is broadly retained: mean margin stays near M62, and M98
  seed9481/seed9482 improve minimum margin.
- Behavior-level self-ID does not pass: reset and zero-response ablations do not
  degrade seed9480 behavior. They slightly improve success.

The likely reason is structural: M98 trained the response hidden to carry
future-envelope information, but did not train the actor head to use that new
belief for action selection.

## Decision

Do not claim closed-loop self-identification.

Do not promote M98 as a driver candidate yet. M98 is a good representation
pretraining checkpoint:

```text
hidden belief: pass
behavior retention: pass
behavior dependence on hidden belief: fail
```

The next step should couple the actor to the M98 hidden belief under retention
guards:

```text
initialize from M98;
freeze or lightly update response encoder / GRU;
train actor head or low-LR PPO with retention anchor;
gate normal vs reset/zero-response/wrong-history behavior again.
```
