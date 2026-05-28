# M1198 Paper-Route Fair Comparison Pilot Design

## Summary

M1198 designs the first fair public comparison pilot after all generated
profiles passed train-loop smoke. It does not train controllers or use the
M1196/M1197 smoke metrics as performance evidence.

Decision:

```text
fair_comparison_pilot_design_admit_public_pilot_run
```

The next milestone may run a public pilot. Its scope is still limited:
engineering comparison evidence, not promotion, private holdout, paper-level
generalization, or self-identification proof.

## Why Smoke Metrics Are Excluded

M1196 and M1197 used:

```text
1024 total steps
one seed per profile
tiny smoke eval
no repeated training seeds
no fixed comparison evaluation corpus
```

Those results prove train-loop plumbing only. They must not be used to claim
that a finite-window controller is better than GRU or vice versa.

## Pilot Profile Set

The first comparison pilot should use seven main profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
```

`L3_reset_control` remains a diagnostic control. It should be evaluated in the
same run directory if cheap, but it is not part of the main performance ranking.

Reason:

```text
L0/L1/L2/L3 answer the paper-route feedback-history question.
L3_reset_control answers a recurrent-state diagnostic question, not the main controller-family comparison.
```

## Training Budget

This is a public pilot, not a final paper experiment.

```text
training_seeds_per_profile: 3
training_seed_offsets: [0, 1, 2]
total_steps_per_seed: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
device: cpu unless cuda is explicitly selected by the run manifest
vector_env_mode: sync for deterministic plumbing; parallel may be a later speed audit
```

The key fairness rule is equal environment interaction budget per profile and
seed. Do not adjust `total_steps`, `num_envs`, `rollout_steps`, reward,
randomization ranges, or eval episodes per profile after seeing early results.

## Evaluation Budget

Use a fixed public eval corpus, not each config's tiny smoke eval alone.

```text
eval_episodes_per_checkpoint: 64
eval_seed_base: 119800
eval_seed_policy: same seeds for every profile checkpoint
eval_env_config: same generated config env distribution unless a separate eval config is written in the pilot manifest
```

Required metrics:

```text
success_rate
collision_rate
road_departure_rate
spin_or_unstable_rate
termination_rate
clearance_margin_mean
clearance_margin_p10
return_mean
steps_mean
control_smoothness
runtime_seconds
parameter_count
observation_dim
```

If the current eval utilities cannot produce all metrics, the pilot run should
record the available metrics and route to an evaluation-metric implementation
milestone before making broader claims.

## Public Claim Scope

Allowed after a successful pilot:

```text
training stability comparison
public pilot engineering performance trend
whether current-only / one-step / finite-window / GRU warrants deeper training
which profile family should receive the next resource budget
```

Not allowed:

```text
paper-level claim
private-holdout claim
promotion
final driver capability claim
GRU recurrent-belief advantage
strong self-identification evidence
sim-to-real claim
```

GRU recurrent-belief advantage requires later current-ambiguous,
variable-delay, same-current/different-older-history, and wrong/delayed/reset
history tests. It cannot come from this pilot alone.

## Failure Rules

If any profile fails to train:

```text
record failure;
do not tune that profile and continue comparing as if fair;
route to a focused repair or resource audit;
restart the comparison protocol after repair if the profile set changes.
```

If one profile appears strong or weak:

```text
do not change only that profile's hyperparameters;
do not promote it;
do not claim superiority from fewer than 3 training seeds and fixed public eval seeds.
```

If all profiles pass but metrics are noisy:

```text
route to a repeated pilot or longer-budget design;
do not escalate to private holdout.
```

## Artifact Requirements

The pilot run should write:

```text
runs/m1199_fair_comparison_pilot/summary.json
runs/m1199_fair_comparison_pilot/profile_seed_rows.csv
runs/m1199_fair_comparison_pilot/eval_rows.csv
runs/m1199_fair_comparison_pilot/profile_aggregate.csv
docs/m1199-paper-route-fair-comparison-pilot-run.md
```

Each row must include:

```text
profile_name
training_seed
config_path
run_dir
checkpoint
training_return_metrics
eval_metrics
finite_metric_flags
runtime_seconds
parameter_count
observation_dim
contract_flags
```

## Next Milestone

```text
experiments/manifests/m1199-paper-route-fair-comparison-pilot-run.json
```

M1199 may run the public pilot under the fixed protocol above. It must still
avoid promotion, private holdout, per-profile tuning, and self-identification
claims.
