# M7 Validation Protocol

Last updated: 2026-05-21

## Purpose

This protocol defines how AutoDrift will decide whether an M7 RL operator is
effective. A high aggregate success rate is not enough. The policy must solve
the emergency task, generalize to held-out vehicle and road conditions, use
closed-loop feedback, and show evidence of self-identification from
observation-action-response history.

The validation target is the driver-like operator defined in
`docs/m7-universal-closed-loop-operator.md`.

## Claims To Prove

M7 should only claim success when the evidence supports all of these claims:

1. The RL operator solves AEB-infeasible obstacle avoidance better than the
   baselines.
2. The same actor generalizes to vehicle and road conditions that were not used
   for training.
3. The actor uses closed-loop feedback and action history, not only a
   single-frame state.
4. The actor does not depend on rule labels or leaked hidden simulator
   parameters.
5. The actor's behavior is smooth, interpretable, and monitorable enough to be
   a plausible real-time control candidate.
6. The actor is drift-capable, not drift-seeking: it can drive stable AES when
   enough and reserve high-sideslip behavior for cases that need it.

If any claim fails, the result is still useful but must be recorded as a bounded
or negative result.

## Primary Benchmark

The primary benchmark is AEB-infeasible obstacle avoidance with randomized
vehicle-road dynamics.

Compare at least these policies on shared seeds:

- `aeb`;
- `aes_heuristic`;
- `envelope_aes`;
- M5 checkpoint;
- M7-A single-step history or recurrent actor;
- M7-B receding-horizon action-sequence actor, executing only the first action.

Report:

- success rate;
- collision rate;
- obstacle completion rate;
- minimum obstacle clearance;
- post-pass recovery rate;
- residual speed at closest approach or collision;
- return;
- lateral RMSE and peak lateral error;
- sideslip error;
- peak sideslip and sideslip duration;
- speed;
- action-rate and steering/brake chatter metrics;
- termination, spin, or off-track rate.

## Bucketed Reporting

Aggregate numbers are not enough. Every benchmark must report hidden-condition
buckets:

- obstacle label: `aes_feasible`, `drift_required`, `unavoidable`;
- friction: low, medium, high, split-mu, friction-step;
- vehicle mass: light, nominal, heavy;
- CG: front-heavy, nominal, rear-heavy;
- brake authority: weak, nominal, strong;
- steering response: slow, nominal, fast;
- tire stiffness or grip: weak, nominal, strong;
- train distribution versus held-out distribution.

The policy should not be called general if one or two easy buckets hide severe
failures elsewhere.

## Scenario-Specific Behavior Quality

The same actor must cover stable and extreme behavior. Evaluate each obstacle
label with a different quality lens:

- `aes_feasible`: success should come with stable avoidance quality, low
  unnecessary sideslip, low action chatter, and clean recovery;
- `drift_required`: success may involve large sideslip, but the policy should
  build rotation deliberately and recover after passing the obstacle;
- `unavoidable`: measure harm reduction, residual speed, and clearance
  improvement rather than binary success alone.

Useful derived metrics:

- unnecessary drift rate in `aes_feasible` episodes;
- peak sideslip and high-sideslip duration;
- post-pass recovery time for heading, sideslip, and lateral error;
- residual speed at closest obstacle approach or collision;
- action smoothness during entry, avoidance, and recovery.

These metrics keep the objective aligned with a professional driver-like
operator: drift is available when needed, not rewarded as a default style.

## Held-Out Generalization

Training and validation must use different vehicle-road families.

Examples:

- train on continuous `mu` randomization, test on fixed extreme `mu`, split-mu,
  and friction-step profiles;
- train on nominal brake balance, test weak-brake and rear-biased/front-biased
  braking;
- train on one mass/CG range, test heavier, lighter, front-heavy, and
  rear-heavy vehicles;
- train on one steering response range, test slow steering and actuator delay;
- train on one obstacle distance/width range, test held-out obstacle geometry.

The claim should be framed by the held-out result. If the policy only works in
the training distribution, it is not yet a universal operator.

## Closed-Loop Feedback Ablations

The core M7 claim is that the actor identifies controllability from feedback.
Run ablations that remove or corrupt the information needed for that behavior:

- `single_frame`: current observation only;
- `no_action_history`: history kept, previous action or actuator history
  removed;
- `no_recurrence`: stacked history only, no recurrent state;
- `shuffled_history`: history order randomly permuted during evaluation;
- `short_history`: history horizon reduced;
- `privileged_leak`: actor receives true hidden parameters, used only as an
  upper-bound comparison;
- `rule_label_leak`: actor receives obstacle or friction labels, used only to
  show why label leakage is not the desired solution.

M7 is convincing only if the full deployable actor beats the no-history and
no-action-history variants on held-out vehicle-road buckets.

## Self-Identification Evidence

The actor should not be required to output named physical parameters. However,
we can inspect whether its hidden state contains information about the hidden
vehicle-road condition.

Recommended probes:

- recurrent hidden state or temporal encoder latent -> friction bucket;
- latent -> brake authority bucket;
- latent -> steering delay bucket;
- latent -> mass/CG bucket;
- latent -> tire-grip bucket;
- latent -> imminent failure risk.

Probe rules:

- probes are diagnostics only and never enter the control loop;
- train probes on frozen policy rollouts;
- evaluate probes on held-out vehicle-road buckets;
- compare probe accuracy against raw single-frame observations and against
  shuffled-history latents.

Current tooling:

```bash
python -m autodrift.latent_probe \
  --checkpoint runs/ppo_m7a_history_seed127/checkpoint.pt \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --episodes 100 \
  --run-dir runs/latent_probe_m7a_history_100eval
```

The probe writes `samples.csv`, `probe_summary.csv`, `summary.json`, and a
manifest. These artifacts are diagnostics only; no probe output is used by the
actor.

The full M7 gate can be run as:

```bash
python -m autodrift.m7_gate \
  --env-config configs/m7_obstacle_aes_weighted_holdout_eval.json \
  --seed-csv runs/<scenario_corpus>/scenario_corpus.csv \
  --episodes 100 \
  --probe-episodes 100
```

The gate writes a single `gate_summary.md` and `summary.json` that combine
baseline comparison, history ablation, stable-AES behavior, and latent-probe
checks.

Useful evidence is not just high probe accuracy. The stronger result is that
probe accuracy and control success both degrade when action history or temporal
order is removed.

## Receding-Horizon Sequence Validation

M7-B outputs an action sequence but executes only the first action:

```text
history_t -> [a_t, a_{t+1}, ..., a_{t+H-1}]
execute a_t
observe next state
repeat
```

Validate M7-B separately from M7-A:

- compare success and collision rates against M7-A;
- report sequence smoothness and action-rate penalties;
- measure shifted consistency between the previous plan tail and the next plan;
- check whether sequence preview can warn about unsafe future intent before
  collision or off-track termination;
- confirm that executing only the first action preserves closed-loop feedback.

M7-B is useful if it improves smoothness, safety preview, or actuator-delay
handling without hurting held-out success.

## Behavior Diagnostics

For selected seeds, save rollout traces and plots:

- trajectory and obstacle clearance;
- steering and drive/brake command;
- action rate;
- speed, yaw rate, sideslip, lateral error;
- recurrent latent or probe outputs over time;
- M7-B predicted sequence at several time points.

Look for:

- high-frequency steering or brake chatter;
- delayed or missing recovery after obstacle pass;
- actions that saturate for long periods without vehicle response;
- overfitting to one obstacle side or one friction bucket;
- unsafe sequence previews before collision.

These diagnostics do not replace benchmark metrics, but they make failures
actionable.

## Minimum Acceptance Gate

An M7 checkpoint passes the first validation gate when:

- it beats AEB, heuristic AES, envelope AES, and the M5 checkpoint on held-out
  `drift_required` obstacle scenarios;
- it matches or improves stable-avoidance quality on held-out `aes_feasible`
  scenarios without unnecessary sideslip;
- it improves or matches collision rate while maintaining obstacle completion;
- it reports recovery quality after obstacle pass;
- it reports bucketed results for vehicle, road, and obstacle conditions;
- the full actor beats `single_frame` and `no_action_history` ablations;
- the actor receives no true hidden parameters and no rule labels at deployment
  time;
- at least one latent probe shows above-baseline information about hidden
  vehicle-road state on held-out rollouts;
- failure cases are documented with traces and bucket summaries.

This gate is for simulation evidence only. It does not claim sim-to-real safety
or real-vehicle readiness.

## Negative Result Policy

Negative results are expected and should be kept:

- if M7-B is smoother but less successful than M7-A, keep both results;
- if recurrent policies overfit, record the bucket where they fail;
- if privileged leakage wins, use it as an upper bound, not as a deployment
  solution;
- if a model-based baseline beats RL in a bucket, document that bucket and use
  it to refine training or safety monitoring.

The goal is a reproducible proof chain, not a single favorable score.
