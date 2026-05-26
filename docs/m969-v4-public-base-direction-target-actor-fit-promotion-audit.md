# M969 V4 Public Base Direction Target Actor-Fit Promotion Audit

## Purpose

M969 audits whether the M964 direction-target actor-fit candidate selected by
M966 and evaluated by M968 should become the new public-gate base.

Candidate:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Previous public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

M969 does not train, run PPO, use private holdout, or change actor inputs.

## Promotion Evidence

### M964 Objective Fit

M964 showed that `alpha=1.0` improves the exported direction-target actor-fit
objective while changing only `actor_mean`.

```text
result_class: direction_target_actor_fit_candidate
candidate_alpha_count: 5
best alpha: 1.0
actor_mean_changed: true
non_actor_mean_changed: false
actor_input_contract_changed: false
ppo_used: false
promoted: false
```

### M966 Public Replay Gate

M966 replay-gated all M964 candidates and selected the highest-ranked passing
candidate.

```text
result_class: direction_target_actor_fit_replay_gate_pass
selected_alpha: 1.0
candidate_preflight_pass_count: 5 / 5
public_replay_gates_passed: 6 / 6
source_diverse_protected_status: pass
behavior_pass: true
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

All six public replay surfaces passed:

```text
M183/M168
M183/M170
M193/M189
M212/M204
M223/M219
M267/M264
```

### M968 Promotion/Generalization Gate

M968 added the required fresh public generalization and behavior checks.

```text
result_class: direction_target_actor_fit_promotion_gate_candidate
proof_pass: true
generalization_pass: true
behavior_pass: true
source_diverse_protected_status: pass
actor_inputs_changed: false
training_started: false
ppo_used: false
promoted: false
```

Fresh public eval:

```text
seed 96700: success delta 0.0, margin delta -0.0005224
seed 96701: success delta 0.0, margin delta -0.0005119
```

Moderate OOD eval:

```text
seed 96720: success delta 0.0, margin delta 0.0005235
```

Behavior seeds:

```text
9505:  pass
9506:  pass
96730: pass
96731: pass
```

For all behavior seeds:

```text
candidate normal success >= reset success >= zero_all success
```

## Promotion Decision

M969 promotes:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

as the new public-gate base.

Decision:

```text
direction_target_actor_fit_promote_public_gate_base
```

This supersedes M399 alpha `0.05` as the active public-gate base for subsequent
public-base research branches.

## Claim Boundary

Supported:

- alpha `1.0` is a stronger public-gate base than M399 for the current
  direction-target actor-fit branch;
- public proof replay remains intact;
- fresh public randomized eval and moderate OOD eval do not materially regress;
- behavior seeds and response ablation ordering are retained;
- actor inputs, recurrent contract, and hidden/oracle restrictions remain
  unchanged.

Not supported:

- paper-level private-holdout generalization;
- real-vehicle transfer;
- high-fidelity four-wheel dynamics claims;
- long PPO continuation safety;
- a claim that alpha `1.0` is globally optimal.

## Post-Promotion Restrictions

After promotion, the next branch must still:

```text
not run long PPO without a new guarded continuation design
not use private holdout for repair
not change actor inputs
not treat public proof rows as paper-level generalization
not discard M399 from comparison lineage
```

## Updated Public-Gate Base

Current public-gate base:

```text
runs/m964_v4_public_base_direction_target_actor_fit/checkpoints/alpha_1_0.pt
```

Previous public-gate base:

```text
runs/m399_s02_interpolation/checkpoints/alpha_0_05.pt
```

## Next Blocker

M969 routes to:

```text
m970-v4-public-base-direction-target-actor-fit-post-promotion-synthesis
```

M970 should synthesize M964-M969 and decide the next branch before any PPO
continuation.
