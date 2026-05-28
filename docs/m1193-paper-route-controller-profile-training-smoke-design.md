# M1193 Paper-Route Controller Profile Training Smoke Design

## Summary

M1193 designs the next training-smoke step for the L0/L1/L2/L3 paper-route
controller comparison. It does not launch training.

The key finding is that training should remain blocked for one more
infrastructure step: `train_ppo` currently builds vector environments directly
from `AutoDriftEnv`, so the M1191 controller-profile observation mask is not yet
applied inside the training entrypoint. Runtime smoke is clean, but L0 training
would still leak previous physical command fields unless the profile mask is
integrated into train/eval vector-env construction.

## Inputs From Prior Milestones

Available profile configs:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

M1192 integrated runtime smoke:

```text
config_count: 8
all_configs_instantiated: true
l0_mask_observed: true
unmasked_profiles_unchanged: true
contract_ok: true
model_forward_ok: true
training_started: false
ppo_used: false
```

Training entrypoint gap:

```text
train_ppo -> make_vector_env -> SyncAutoDriftVectorEnv / ParallelAutoDriftVectorEnv
vector envs construct AutoDriftEnv directly
controller_profile_runtime wrapper is not yet applied there
```

## Protocol Decision

Do not run profile training next.

First satisfy the workflow synthesis cadence, then implement
training/evaluation entrypoint runtime-mask integration:

```text
M1194:
  paper-route finite-window vs GRU infrastructure synthesis

M1195 if synthesis continues:
  controller-profile train-entrypoint runtime-mask integration
  no controller training
  no PPO
  focused tests proving vector-env reset/step observations apply L0 mask
```

Only after synthesis and the follow-up train/eval mask integration should a
training smoke run start.

## Training-Smoke Protocol After Synthesis And Mask Integration

### Stage A: Minimal Training Plumbing Smoke

Purpose:

```text
prove each controller class can run the training loop without NaN, shape error,
mask leak, recurrent-state error, or artifact failure
```

Profiles:

```text
L0_current_masked
L1_one_step
L2_window_25
L3_online_gru
```

Budget:

```text
total_steps: 1024
rollout_steps: 64
num_envs: 2
update_epochs: 1
minibatch_size: 128
device: cpu
seeds: [119400]
```

Acceptance:

```text
each run completes
checkpoint or final model artifact is written
train metrics and eval summary are finite
L0 observations are masked in vector training path
no hidden/oracle/wheel/slip/reference/TTC actor inputs
no private holdout
no promotion
no performance comparison claim
```

### Stage B: Full Generated Profile Smoke

Run only if Stage A passes.

Profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
L3_reset_control
```

Budget:

```text
same as Stage A
seeds: [119500]
```

Purpose:

```text
prove all generated profile configs are train-loop compatible under the same
smoke budget
```

### Stage C: Fair Comparison Pilot

Run only after Stage B and a separate comparison manifest.

Profiles:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_25
L2_window_50
L2_window_100
L3_online_gru
```

L3 reset-control remains a diagnostic control, not a main performance profile.

Budget:

```text
same env distribution
same reward
same action contract
same total environment steps per seed
same seed set per profile
same eval seeds
no per-profile hyperparameter tuning from early results
```

The first fair comparison pilot should still be framed as training stability
and plumbing evidence. It should not claim finite-window or GRU superiority.

## Metrics To Record

Smoke metrics:

```text
completed
returncode
artifact paths
finite_loss
finite_value
finite_policy_loss
checkpoint_written
eval_summary_written
mask_applied_for_l0
actor_input_contract_ok
runtime_seconds
peak profile observation_dim
parameter_count
```

Later comparison metrics:

```text
success_rate
collision_rate
road_departure_rate
spin_rate
clearance_margin_mean
clearance_margin_tail
control_smoothness
termination histogram
capacity and inference cost
```

Self-identification metrics remain out of scope until a dedicated mechanism
manifest:

```text
wrong-history degradation
reset-history degradation
delayed-history degradation
same-current different-older-history tests
future envelope prediction
```

## Fairness Rules

The following are fixed before training:

```text
same generated config family
same obstacle/task distribution
same randomization ranges
same action contract
same reward and termination rules
same total_steps per seed
same eval episode count for smoke
same public gate stack for admission
same no-private-holdout rule
same no-hidden/no-oracle actor-input contract
```

Do not tune hyperparameters after seeing one profile's result and then compare
against other profiles. If a profile-specific repair is required, it creates a
new protocol and invalidates direct comparison against earlier runs.

## Resource Cap

The first training smoke must stay CPU-bounded:

```text
Stage A max profiles: 4
Stage A max seeds: 1
Stage A max total_steps per profile: 1024
Stage A max num_envs: 2
Stage A expected runtime: smoke-scale only
```

If L2_window_100 is too expensive in Stage B, keep it as a generated config but
route to a separate resource audit rather than silently dropping it from the
paper matrix.

## Failure Taxonomy

Use these labels:

```text
contract_violation
training_instability
metric_artifact
scenario_sampling_failure
seed_fragility
behavior_regression
none
```

For smoke runs, the most important failure types are:

```text
contract_violation: mask not applied or forbidden actor input appears
training_instability: NaN, shape mismatch, optimizer failure, recurrent-state failure
metric_artifact: smoke summary reports success without actually writing required artifacts
```

## Next Milestone

```text
experiments/manifests/m1194-paper-route-finite-window-gru-infrastructure-synthesis.json
```

M1194 should synthesize the M1184-M1193 paper-route infrastructure branch
before another implementation milestone. If the synthesis decision is
`continue`, the next implementation should integrate controller-profile runtime
masks into train/eval entrypoints or vector env wrappers, then prove with
focused tests that L0 vector reset/step observations are masked while unmasked
profiles remain unchanged.

## Decision

```text
training_smoke_design_routes_to_branch_synthesis_before_mask_integration
```

M1193 passes as a design milestone because it prevents a false L0 training
comparison and routes to the required workflow synthesis before the necessary
entrypoint integration.
