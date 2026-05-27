# M1068 V4 Public Base Expanded-Gate Medium PPO Design

## Purpose

M1068 designs the first conservative medium PPO escalation after the short-PPO
promotion, refreshed family-intersection proof surface, expanded gate
integration, and M1067 propagation fix.

This milestone does not train, run PPO, use private holdout, change actor
inputs, or promote a checkpoint.

## Base

Start from the current public-gate base:

```text
runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

This is the M1052-promoted 4096-step checkpoint. The design uses it as both:

```text
init_checkpoint
baseline/snippet action anchor checkpoint
```

so the medium proposal is anchored to the current base, not the older M1044
base.

## Step Budget

M1069 should run one conservative medium-ramp PPO proposal:

```text
total_steps: 8192
seed_count: 1
seed: 61069
promotion: blocked
private_holdout: blocked
```

Reason:

```text
4096 steps is already repeatable across three seeds.
8192 doubles the short budget without jumping to 16k or long-run PPO.
The goal is to test whether the expanded gate stack survives a medium-ramp
proposal, not to make a medium/long stability claim.
```

If M1069 passes, the next step should be a fresh-seed 8192-step repeat before
any promotion or 16k escalation.

## Config

Created:

```text
configs/ppo_m1069_expanded_gate_medium_seed61069.json
```

Changes versus `configs/ppo_m1049_guarded_short_escalation_seed61049.json`:

```text
total_steps: 4096 -> 8192
checkpoint_interval_steps: 4096 -> 8192
seed: 61049 -> 61069
baseline_action_anchor_checkpoint:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
snippet_action_anchor_checkpoint:
  runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt
```

Kept unchanged:

```text
rollout_steps: 128
num_envs: 8
minibatch_size: 512
learning_rate: 5e-7
freeze_log_std: true
vector_env_mode: parallel
vector_env_start_method: fork
training_seed_mix_probability: 0.35
response_prediction_aux_coef: 0.06
outcome_intervention_aux_coef: 0.06
rejected_history_preference_aux_coef: 0.03
baseline/snippet/trajectory anchor coefficients
randomization ranges
actor input contract
```

No new loss terms are added in M1069. This isolates the effect of step-budget
escalation under the expanded gate stack.

## Command

M1069 should use the guarded PPO wrapper:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1049_guarded_short_escalation_seed61049/checkpoint.pt \
  --config configs/ppo_m1069_expanded_gate_medium_seed61069.json \
  --run-dir runs/m1069_expanded_gate_medium_ppo_seed61069 \
  --ppo-run-dir runs/ppo_m1069_expanded_gate_medium_seed61069 \
  --device auto
```

The wrapper name still says `smoke`; the config determines the true PPO step
budget.

## Expanded Gate Stack

M1069 must pass:

```text
1. PPO completes and writes a raw checkpoint.
2. Training metrics are finite.
3. Actor input contract is unchanged.
4. Exact M997 temporal retention passes.
5. Exact M297/M270 no-regression passes.
6. Combined active-set loss gate passes.
7. Six old public proof replay surfaces pass.
8. M1061 family-intersection public gate passes.
9. Three source-diverse protected diagnostics pass.
10. Fresh public seeds 103900/103901 do not regress.
11. Moderate-OOD seed 103920 does not regress.
12. Behavior seeds 9505/9506/103930/103931 retain ordering.
```

Important: after M1067, the outer guarded PPO wrapper computes:

```text
proof_pass = public_replay_pass && family_intersection_pass
```

so a family-intersection failure must produce:

```text
combined_active_set_guarded_ppo_public_replay_washout
failure_types: proof_washout
```

## Hard Rollback Rules

M1069 must be rejected if any of these occur:

```text
actor_inputs_changed == true
ppo_returncode != 0
training_metrics_finite == false
exact_pass == false
public_replay_pass == false
family_intersection_pass == false
source_diverse_pass == false
generalization_pass == false
behavior_pass == false
```

Hard row checks:

```text
M267/M264 row15:
  wrong_history_success must remain false
  wrong_history_margin must remain < 0
  success_drop_count must remain 17 / 17

M183/M170 row16:
  normal_success must remain true
  normal_margin must remain > 0
  success_drop_count must remain 17 / 17

M1061 family-intersection:
  short61049 source rows retain 25 / 25 success drops
  short61050 source rows retain 27 / 27 success drops
  short61051 source rows retain 27 / 27 success drops
```

Any hard rollback failure is `proof_washout` even if aggregate fresh/OOD
metrics improve.

## Promotion Rule

M1069 cannot promote.

If M1069 passes all gates:

```text
route to 8192-step fresh-seed repeat
```

If M1069 fails:

```text
training instability -> recipe audit
exact/proof/family gate failure -> localized proof-washout audit
source-diverse failure -> source diagnostic audit
fresh/OOD failure -> generalization regression audit
behavior failure -> behavior regression audit
```

## Decision

```text
expanded_gate_medium_ppo_design_admit_m1069_single_seed_run
```

Next:

```text
m1069-v4-public-base-expanded-gate-medium-ppo-smoke
```
