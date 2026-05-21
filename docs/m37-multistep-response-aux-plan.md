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
