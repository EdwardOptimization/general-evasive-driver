# M1384 Paper-Route History-Profile Fixed-Budget Refresh Design

## Purpose

M1384 designs a fresh fixed-budget L0/L1/L2/L3 profile refresh after M1383
showed that old M1212 profile checkpoints and the current M1362 public base are
not directly comparable as a fair architecture-ranking result.

This milestone is design-only. It does not train, run PPO, run new evaluation,
promote a checkpoint, use private holdout, export a corpus, change actor inputs,
or claim a profile-ranking result.

## Design Decision

Admit a staged refresh:

```text
M1385: corrected-profile runtime smoke, no training
M1386: one-seed fixed-budget training/eval smoke, public diagnostic only
M1387: audit M1386 before any 3-seed pilot
```

Do not jump straight to a 3-seed or longer profile pilot. The profile runner is
usable, but this branch must first verify that the corrected configs still
instantiate cleanly in the current codebase and that all eight profiles can
complete one matched fixed-budget seed.

## Profile Set

Use the corrected profile set from M1207:

```text
L0_current_masked
L1_one_step
L2_window_13
L2_window_13_current_tiled
L2_window_25
L2_window_25_current_tiled
L3_online_gru
L3_reset_control_corrected
```

Required controls:

```text
current-tiled L2 controls:
  L2_window_13_current_tiled
  L2_window_25_current_tiled

corrected L3 reset control:
  L3_reset_control_corrected
```

The current-tiled controls and corrected reset control are not optional. If they
fail runtime or training smoke, the branch must route to profile-control repair
instead of running comparisons.

## Stage 0: Runtime Smoke

Milestone:

```text
m1385-paper-route-history-profile-corrected-runtime-smoke
```

Command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.controller_profile_runtime_smoke \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --seed 138500 \
  --run-dir runs/m1385_history_profile_corrected_runtime_smoke
```

Pass requirements:

```text
result_class == controller_profile_runtime_smoke_pass
profile_count == 8
current_tiled_profile_count == 2
current_tiled_profiles_observed == true
corrected_reset_profile_count == 1
all_configs_instantiated == true
forbidden-input flags remain false
```

No training, PPO, promotion, private holdout, corpus export, or profile-ranking
claim is allowed.

## Stage 1: One-Seed Fixed-Budget Smoke

This stage should run only after M1385 passes.

Candidate command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.corrected_profile_pilot \
  --config-dir configs/paper_route_corrected_profiles \
  --config-glob 'm1207_*.json' \
  --run-dir runs/m1386_history_profile_fixed_budget_smoke \
  --training-seed-base 138600 \
  --seed-offsets 0 \
  --eval-seed-base 138700 \
  --eval-episodes 32 \
  --device cpu
```

The source configs already use the corrected public-pilot budget:

```text
total_steps: 8192
rollout_steps: 128
num_envs: 4
update_epochs: 2
minibatch_size: 256
vector_env_mode: sync
```

One-seed pass requirements:

```text
profile_count == 8
total_seed_runs == 8
completed_seed_runs == 8
failed_seed_runs == 0
all_eval_metrics_finite == true
private_holdout_used == false
promoted == false
profile_specific_tuning == false
actor_input_contract_changed == false
```

Interpretation:

```text
valid training/eval plumbing only
no architecture ranking
no paper-level claim
no self-identification claim
```

## Stage 2: Three-Seed Public Pilot

This stage should be designed or admitted only after the one-seed smoke is
audited.

Candidate scale:

```text
training_seed_base: 138800
seed_offsets: 0,1,2
eval_seed_base: 138900
eval_episodes: 64
device: cpu unless a separate same-device CUDA policy is pre-registered
```

Public-pilot pass requirements:

```text
24 / 24 profile-seed runs complete
all selected metrics finite
same eval seeds for every profile checkpoint
private_holdout_used == false
profile_specific_tuning == false
actor_input_contract_changed == false
```

The public pilot may report trends, but it must route to an audit before any
longer run, private holdout, or profile ranking claim.

## Metric And Claim Rules

Required comparisons:

```text
L1_one_step - L0_current_masked
L2_window_13 - L2_window_13_current_tiled
L2_window_25 - L2_window_25_current_tiled
L3_online_gru - L3_reset_control_corrected
L3_online_gru - L1_one_step
L3_online_gru - L2_window_25
```

Required metrics:

```text
success_rate
collision_rate
clearance_margin_mean
clearance_margin_p10
return_mean
termination_rate
steps_mean
control_smoothness
spin_or_unstable_rate
parameter_count
runtime_seconds
```

Interpretation order:

```text
1. artifact completeness and finite metrics
2. current-frame substitution controls
3. finite-window normal vs current-tiled controls
4. online GRU vs corrected reset-control
5. public aggregate profile trend
6. source-rich temporal diagnostics only after standard public pilot is valid
```

Claim boundaries:

```text
L2 normal not beating current-tiled:
  no finite-window history-necessity claim.

L3 online not beating corrected reset:
  no recurrent-hidden utility claim.

L3 beating reset but not L1/L2:
  recurrent hidden may help the L3 family, but architecture superiority is not
  supported.

Any one-seed result:
  plumbing only, not evidence ranking.

Any public 3-seed result:
  public trend only, not private holdout or paper-level ranking.
```

## M1362 Anchor Policy

M1362 remains the current public-gate base and should be reported as a separate
diagnostic anchor:

```text
public-base L3 diagnostic anchor: allowed
fixed-budget architecture-ranking participant: not allowed
checkpoint mutation to add metadata: not allowed
```

If a later runner needs M1362 metadata, use a sidecar/adaptor and keep the
artifact immutable.

## Next Route

Decision:

```text
history_profile_fixed_budget_refresh_design_admit_runtime_smoke
```

Next milestone:

```text
m1385-paper-route-history-profile-corrected-runtime-smoke
```

M1385 should run only the runtime smoke. If it passes, the next route can be a
one-seed fixed-budget smoke. If it fails, route to profile-control repair.

## Guardrails

M1384 performs no training, PPO, new evaluation, actor update, checkpoint
mutation, promotion, private holdout, threshold relaxation, actor-input
expansion, corpus export, high-fidelity claim, paper-level profile-ranking
claim, or level3 self-identification claim.
