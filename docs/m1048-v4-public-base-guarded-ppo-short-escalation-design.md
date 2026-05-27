# M1048 V4 Public Base Guarded PPO Short Escalation Design

## Purpose

M1048 designs the first PPO escalation beyond the 1024-step guarded smoke
scale after M1047 passed two fresh-seed smoke repeats.

This milestone does not train, run PPO, use private holdout, change actor
inputs, promote a checkpoint, or claim long-run PPO stability.

## Current Public-Gate Base

```text
runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt
```

M1044 promoted this checkpoint through M1045 after one 1024-step guarded PPO
proposal passed the full public gate. M1047 then ran two fresh 1024-step
guarded PPO repeats from the same base:

```text
seeds: 61045, 61046
exact_pass_count: 2 / 2
proof_pass_count: 2 / 2
source_diverse_pass_count: 2 / 2
generalization_pass_count: 2 / 2
behavior_pass_count: 2 / 2
actor_inputs_changed_count: 0 / 2
promoted: false
private_holdout_used: false
```

That evidence supports moving beyond smoke scale, but only as a bounded
short-escalation proposal.

## Escalation Decision

M1049 should run one short PPO proposal:

```text
total_steps: 4096
seed_count: 1
seed: 61049
promotion: blocked
private_holdout: blocked
```

The step count is deliberately conservative. It is four times the smoke budget
used by M1044/M1047, so it tests whether the guarded recipe survives a longer
closed-loop PPO update, but it is still far below medium or long PPO.

M1049 should not run multiple 4096-step seeds in the same milestone. If the
single short proposal passes the full gate stack, the next milestone should be
a fresh-seed short-repeat gate. This keeps the failure localization clean:

```text
M1049:
  does a 4096-step proposal remain feasible?

M1050 if M1049 passes:
  is that 4096-step feasibility repeatable across fresh PPO seeds?
```

## M1049 Config

Create:

```text
configs/ppo_m1049_guarded_short_escalation_seed61049.json
```

Start from the M1047 seed config and change only:

```text
total_steps: 4096
checkpoint_interval_steps: 4096
seed: 61049
```

Keep these PPO controls unchanged:

```text
rollout_steps: 128
num_envs: 8
minibatch_size: 512
learning_rate: 5e-7
freeze_log_std: true
vector_env_mode: parallel
vector_env_start_method: fork
training_seed_mix_probability: 0.35
```

Keep these retention signals unchanged:

```text
M997 temporal sequence corpus
M270 source-balanced outcome intervention corpus
M297 rejected-history preference corpus
M1037 combined active-set row16x4 anchor
baseline action anchor from the M1045 public-gate base
snippet action anchor from the M1045 public-gate base
```

Do not add new loss terms in M1049. The milestone should test the current
guarded recipe at a longer PPO horizon, not confound escalation with recipe
changes.

## Command

M1049 should use the existing guarded PPO wrapper:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.combined_active_set_guarded_ppo_smoke \
  --base-checkpoint runs/ppo_m1044_combined_active_set_guarded_smoke_seed61044/checkpoint.pt \
  --config configs/ppo_m1049_guarded_short_escalation_seed61049.json \
  --run-dir runs/m1049_guarded_ppo_short_escalation_seed61049 \
  --ppo-run-dir runs/ppo_m1049_guarded_short_escalation_seed61049 \
  --device auto
```

The wrapper name still says `smoke`, but the config controls the PPO step
budget. M1049 should record the true `total_steps=4096` in its manifest and
milestone document.

## Gate Stack

M1049 must use the same public gate stack as M1044/M1047:

```text
1. PPO completes and writes a raw checkpoint.
2. Training metrics are finite.
3. Actor input contract is unchanged.
4. Exact M997 temporal retention passes.
5. Exact M297/M270 no-regression passes.
6. Combined active-set loss gate passes.
7. All six public proof replay surfaces pass.
8. Three source-diverse protected diagnostics pass.
9. Fresh public seeds 103900/103901 do not regress.
10. Moderate-OOD seed 103920 does not regress.
11. Behavior seeds 9505/9506/103930/103931 retain ordering.
```

The six public proof replay surfaces remain:

```text
m183_m168
m183_m170
m193_m189
m212_m204
m223_m219
m267_m264
```

The three source-diverse diagnostics remain:

```text
current_m333_surface
m317_continuity_surface
m314_continuity_surface
```

## Hard Rollback Rows

M1049 must explicitly report these rows:

```text
M267/M264 row15:
  wrong_history_success must remain false
  wrong_history_margin must remain < 0
  M267/M264 success_drop_count must remain 17 / 17

M183/M170 row16:
  normal_success must remain true
  normal_margin must remain > 0
  M183/M170 success_drop_count must remain 17 / 17
```

If either row flips polarity, classify the result as `proof_washout` even if
fresh/OOD aggregate behavior improves.

## Promotion Rule

M1049 cannot promote.

If M1049 passes all gates, route to a short-escalation fresh-seed repeat before
any public-base promotion or medium PPO:

```text
m1050-v4-public-base-guarded-ppo-short-escalation-repeat
```

If M1049 fails exact or proof gates, route to a localized failure audit before
changing the recipe:

```text
exact/proof failure:
  guarded_ppo_short_escalation_failure_audit

training instability:
  guarded_ppo_short_escalation_recipe_audit

generalization or behavior regression:
  guarded_ppo_short_escalation_generalization_or_behavior_audit
```

## Public Overfit Risk

Risk remains moderate. The hard rows and replay surfaces are public, and the
active-set anchor is built from known public proof failures. M1049 is still
allowed because it is not a promotion milestone, it keeps private holdout
blocked, and it asks a narrow process question: whether the already validated
guarded recipe survives a longer PPO proposal.

## Decision

```text
guarded_ppo_short_escalation_design_admit_m1049_short_smoke
```

Next:

```text
m1049-v4-public-base-guarded-ppo-short-escalation-smoke
```
