# M315 Protected-Key-Aware PPO Proposal Repeat Design

M315 designs the next repeat after M314 promoted M313 alpha `0.14` as the
public-gate base. No PPO was run, no repair was run, and actor inputs are
unchanged.

## Design Decision

M310/M314 showed the correct acceptance stack:

```text
PPO raw proposal
  -> exact M297/M270 repair
  -> protected-key-bounded interpolation
  -> first replay gates
  -> full public promotion gate
```

M316 should use that stack from the start. A raw PPO checkpoint is only a
proposal; an exact-repaired checkpoint is still not enough if it violates
protected key `9944`.

## M316 PPO Proposal

Config:

```text
configs/ppo_m316_protected_key_aware_proposal_smoke.json
```

Initial checkpoint and PPO anchors:

```text
runs/m313_m307_to_m310_protected_key_bounded_interpolation/checkpoints/alpha_0_14.pt
```

Smoke settings:

| Field | Value |
| --- | ---: |
| total_steps | 1024 |
| rollout_steps | 128 |
| num_envs | 8 |
| learning_rate | 5e-7 |
| seed | 5235 |
| rejected_history_preference_aux_coef | 0.03 |
| outcome_intervention_aux_coef | 0.06 |
| baseline_action_anchor_coef | 100.0 |
| snippet_action_anchor_coef | 100.0 |
| trajectory_action_anchor_coef | 100.0 |

## Acceptance Order

M316 should use this order:

```text
1. Train raw PPO proposal from M314 base.
2. Run exact post-PPO repair from raw.
3. Generate base-to-repaired interpolation sweep.
4. Evaluate exact M297/M270 on alphas.
5. Evaluate protected key 9944 on alphas.
6. Select largest nonzero alpha passing exact and protected-key gates.
7. Run M183/M170 and M267/M264 first replay gates.
8. Admit full public gate only if first gates pass.
```

Because M314 base is already close to the protected-key normal-margin upper
window, the alpha grid should include small values:

```text
0, 0.0025, 0.005, 0.01, 0.02, 0.05, 0.1, 0.14, 0.2, 0.5, 1.0
```

## Decision

Admit:

```text
m316-protected-key-aware-ppo-proposal-smoke
```

Decision:

```text
admit_m316_protected_key_aware_ppo_proposal_smoke
```
