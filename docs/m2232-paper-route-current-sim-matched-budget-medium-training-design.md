# M2232 Paper-Route Current-Sim Matched-Budget Medium Training Design

- status: completed
- decision: `current_sim_matched_budget_medium_training_design_admit_config_materialization`
- manifest: `experiments/manifests/m2232-paper-route-current-sim-matched-budget-medium-training-design.json`
- parent audit: `docs/m2231-paper-route-current-sim-matched-budget-profile-training-execution-result-audit.md`

## Rationale

M2230 cleanly completed the short-v0 matched-budget training panel:

- completed runs: `15/15`
- failed runs: `0`
- finite selected metrics: `true`
- contract violations: `0`
- guardrail violations: `0`

but all profiles failed the pre-registered readiness floor:

- quality_floor_profile_pass_count: `0`
- each profile had fewer than `2/3` seeds with eval termination `<=0.4`
  and eval return `>=50.0`.

M2231 classifies this as a training-readiness floor failure, not an
implementation or input-contract failure. The next controlled test is whether
the short-v0 budget was simply too small.

## Medium-v1 Protocol

Keep the same profile/seed panel:

```text
L0_current_masked
L1_one_step
L2_window_25
L2_window_50
L3_online_gru
```

```text
222601
222602
222603
```

Use one matched budget across all profiles and seeds:

```text
total_steps=32768
rollout_steps=128
num_envs=4
update_epochs=2
minibatch_size=256
learning_rate=0.0001
clip_coef=0.1
max_grad_norm=0.25
eval_episodes=32
device=cpu
vector_env_mode=sync
```

Keep the M2226/M2231 readiness floor unchanged:

```text
at least 2/3 seeds per profile with eval_termination_rate <= 0.4
and eval_return_mean >= 50.0
```

## Controls

The design keeps these fixed:

- actor input contract: `P0_human_view_no_wheel_no_oracle`
- wheel observations: `none`
- obstacle relative velocity mode: `zero`
- hidden/oracle actor inputs: forbidden
- profile-specific hyperparameter tuning: forbidden
- private holdout: unused
- winner selection: forbidden
- finite-window-vs-GRU conclusion: forbidden
- level3 self-ID claim: forbidden

## Next

Pre-register materialization:

```text
m2233-paper-route-current-sim-matched-budget-medium-training-config-materialization
```

M2233 should produce deterministic medium-v1 configs and a command matrix only.
Actual medium-v1 training should remain blocked until the materialized artifacts
are clean.
