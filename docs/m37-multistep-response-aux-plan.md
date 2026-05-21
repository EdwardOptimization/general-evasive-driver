# M37 Multi-Step Response Auxiliary Plan

Last updated: 2026-05-21

## Motivation

M34 added one-step response prediction and M36 added response-change hard-corpus
fine-tuning. Both failed the hidden-swap gate. The result suggests the current
auxiliary objective is too local: it can make the policy sensitive to current
response features, but it does not make recurrent hidden state action-relevant.

M37 should extend the auxiliary target from next-frame response prediction to
multi-step future response prediction under the observed closed-loop rollout.
This remains deployable because the target is future observable ego response,
not hidden friction, vehicle parameters, controller mode, or labels.

## Design

Add PPO config fields:

```text
response_prediction_horizon
response_prediction_stride
```

For `response_prediction_horizon > 1`, the response head should predict a
sequence of future response features:

```text
obs[t + 1], obs[t + 2], ..., obs[t + horizon]
```

restricted to the first `response_prediction_dim` human-view features. The loss
must mask episode boundaries and truncated sequence tails.

Important constraints:

- actor observation contract remains unchanged;
- no hidden vehicle parameters or friction labels enter actor input;
- old checkpoints may initialize all compatible weights while reinitializing
  the resized response-prediction head;
- tests must cover target construction, masking across dones, checkpoint
  partial init, and train smoke.

## Implementation

Implemented fields:

```text
PPOConfig.response_prediction_horizon
PPOConfig.response_prediction_stride
```

`ActorCritic.response_prediction_head` now outputs:

```text
response_prediction_dim * response_prediction_horizon
```

and reshapes predictions to:

```text
[rollout_step, env, horizon, response_dim]
```

`build_response_prediction_targets(...)` constructs the future response target
and masks sequence tails or any future that crosses an episode boundary.

Checkpoint initialization now treats response-prediction head shape mismatch
as the same restricted partial-init case as adding the head: all compatible
actor, critic, encoder, GRU, and log-std weights load; only the resized response
head is reinitialized.

Config:

```text
configs/ppo_m37_multistep_response_aux_driver.json
```

Key choices:

- init checkpoint: `M34_151`;
- response horizon: 4;
- response stride: 1;
- response dimension: first 12 human-view response/action-state features;
- response auxiliary coefficient: 0.03;
- M35 response-change corpus mix probability: 0.60;
- total steps: 300k.

## Smoke

Command:

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m37_multistep_response_aux_driver.json \
  --total-steps 4096 \
  --rollout-steps 128 \
  --seed 1637 \
  --device cuda \
  --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --run-dir runs/ppo_m37_multistep_response_aux_smoke_seed1637
```

Result:

- init load mode: `partial_response_prediction_head`;
- training device: `cuda`;
- final smoke step: 4096;
- rollout return mean: 34.42;
- eval return mean: 70.445;
- eval steps mean: 66.200;
- eval termination rate: 0.100.

Smoke conclusion: the multi-step response auxiliary path trains end to end and
can initialize from one-step response checkpoints by resizing only the response
head.

## Validation

M37 should be validated against:

- M35 response-change corpus sweep;
- M29 selected-corpus sweep;
- broad 40-seed sweep;
- hidden-swap gate on the best checkpoint;
- reset and zero-response outcome-change counts.

Success requires more than aggregate success. A useful M37 checkpoint must show
unfavorable hidden/reset/zero-response ablation sensitivity on accepted matched
cases while staying near M30/M34 broad success.

## Full Run Command

```bash
conda run -n autodrift python -m autodrift.train_ppo \
  --config configs/ppo_m37_multistep_response_aux_driver.json \
  --seed 1637 \
  --device cuda \
  --init-checkpoint runs/ppo_m34_response_aux_mixed_seed1434/checkpoints/checkpoint_step_151552.pt \
  --run-dir runs/ppo_m37_multistep_response_aux_seed1637
```

## Full Run Result

Final eval:

- return mean: 70.028;
- steps mean: 66.300;
- termination rate: 0.100;
- lateral RMSE mean: 0.796;
- beta absolute error mean: 0.131.

M35 response-change corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.4625 | 40.454 | 0.5375 |
| M30_053 | 0.6125 | 49.446 | 0.3875 |
| M34_151 | 0.6125 | 48.768 | 0.3875 |
| M36_028 | 0.6125 | 48.934 | 0.3875 |
| M37_053 | 0.6375 | 49.930 | 0.3625 |
| M37_102 | 0.6500 | 50.262 | 0.3500 |
| M37_151 | 0.6125 | 48.285 | 0.3875 |
| M37_200 | 0.6250 | 48.826 | 0.3750 |
| M37_253 | 0.6250 | 49.052 | 0.3750 |
| M37_final | 0.6125 | 48.335 | 0.3875 |

M29 selected-corpus sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.725 | 61.882 | 0.275 |
| M30_053 | 0.875 | 70.795 | 0.125 |
| M34_151 | 0.875 | 69.411 | 0.125 |
| M37_053 | 0.875 | 68.690 | 0.125 |
| M37_102 | 0.875 | 68.293 | 0.125 |
| M37_final | 0.875 | 68.785 | 0.125 |

Broad 40-seed sweep:

| Policy | Success | Return mean | Collision rate |
| --- | ---: | ---: | ---: |
| envelope AES | 0.675 | 56.594 | 0.300 |
| M30_053 | 0.825 | 67.732 | 0.175 |
| M34_151 | 0.825 | 65.783 | 0.175 |
| M37_053 | 0.825 | 64.440 | 0.175 |
| M37_102 | 0.825 | 63.699 | 0.175 |
| M37_final | 0.800 | 63.317 | 0.200 |

M37_102 hidden-swap gate:

- accepted visible matches at 80 episodes: 73 / 80;
- accepted visible matches at 300 episodes: 280 / 300;
- hidden-swap outcome changes: 0 in both gates;
- perturbed reset outcome changes: 2 / 80 and 5 / 300, all unfavorable;
- perturbed zero-response outcome changes: 2 / 80 and 5 / 300, all
  unfavorable.

## Conclusion

M37 is a partial positive result. Multi-step response prediction improves the
M35 response-change corpus while preserving M29 and broad success. It also
turns reset and zero-response ablations into consistently unfavorable outcome
changes on perturbed accepted cases.

It is not a self-identification pass. Hidden-swap still changes zero accepted
success outcomes. The next step is M38/M39: mine M37_102's new unfavorable
response-critical cases, then test whether continued multi-step training can
make the recurrent hidden state itself more behavior-critical.
