# M227 PPO Smoke Retention Failure Audit

M227 audits why M226 failed after starting PPO from the stable M224 actor-update
checkpoint. No PPO is run in this milestone.

Actor inputs are unchanged.

## Question

M224 and M225 used small supervised actor updates on the M223 boundary-outcome
corpus and preserved all replay/protected-key surfaces. M226 used a tiny guarded
PPO smoke from M224 and kept broad behavior, but lost one old replay row and the
historical protected key.

The audit question is:

```text
Does the PPO recipe protect the same proof-surface actions that made the
M224/M225 actor updates stable?
```

## Evidence

Stable actor-update evidence:

| Milestone | Mechanism | Fixed M223 loss | M183 M170 drops | Protected key normal margin | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| M224 | preferred-only snippet action anchor | 0.209824 | 17 / 17 | 0.186385 | pass |
| M225 seed10064 | preferred-only snippet action anchor | 0.210094 | 17 / 17 | 0.190592 | pass |
| M225 seed10065 | preferred-only snippet action anchor | 0.210036 | 17 / 17 | 0.188994 | pass |

M226 PPO evidence:

| Milestone | Mechanism | Fixed M223 loss | M183 M170 drops | Protected key normal margin | Decision |
| --- | --- | ---: | ---: | ---: | --- |
| M226 seed5218 | rollout-state action anchor | 0.209834 | 16 / 17 | 0.203847 | fail |

Broad behavior did not collapse:

| Seed | Policy | Success | Reset success | Zero-all success |
| ---: | --- | ---: | ---: | ---: |
| 9505 | m226_5218 | 0.8625 | 0.8500 | 0.8000 |
| 9506 | m226_5218 | 0.8625 | 0.8500 | 0.8000 |

The failure is therefore not a general driving regression. It is proof-surface
retention washout.

## Code Path Audit

`outcome_intervention_optimize.py`, used by M224/M225, has two relevant anchors:

```text
action_anchor_coef
snippet_action_anchor_coef
snippet_action_anchor_preferred_only = true
```

The important one for M224/M225 is the snippet anchor. It evaluates the anchor
checkpoint directly on the boundary-outcome snippet observations and preferred
hidden states, then penalizes action drift on those exact proof-surface states.

`train_ppo.py`, used by M226, has:

```text
outcome_intervention_aux_coef
baseline_action_anchor_coef
baseline_action_anchor_checkpoint
```

The baseline action anchor is collected from PPO rollout states. It does not
anchor the M223 or M183 proof-surface snippet states. The M226 config includes
the M223 outcome intervention corpus as an auxiliary objective, but it does not
include the preferred-only snippet action anchor that stabilized M224/M225.

## Diagnosis

M226 failed because the PPO guard protects ordinary rollout behavior more than
boundary proof-surface behavior.

This explains the mixed result:

- broad behavior seeds stay at `0.8625` success;
- M223 fixed loss remains close to M224;
- one old M183 M170 normal-history success/drop row is lost;
- protected key `9944|perturbed|28|28` moves outside the near-boundary window
  with normal margin `0.203847 > 0.2`.

The current PPO recipe is not allowed to continue or repeat, because lengthening
it would optimize a path that already showed proof washout.

## Decision

M226 remains rejected.

Failure taxonomy:

```text
proof_washout
protected_key_window_failure
```

Current best remains:

```text
runs/m224_m219_actor_coupling_snippet_pref_anchor100_s10_lr5e5_seed10063/optimized_checkpoint.pt
```

## Next Step

Pre-register M228:

```text
m228-ppo-snippet-action-anchor-implementation
```

M228 should add PPO support for snippet-level action anchoring before any more
PPO smoke. The intended PPO guard is:

```text
outcome_intervention_aux_coef
+ rollout-state baseline_action_anchor_coef
+ boundary snippet_action_anchor_coef
```

The snippet anchor should default to preferred-only hidden/action states for the
proof surface, matching the M216/M224/M225 recipe. M228 is an infrastructure
milestone; it should implement and test the training-time loss path, not claim a
new driver checkpoint.
