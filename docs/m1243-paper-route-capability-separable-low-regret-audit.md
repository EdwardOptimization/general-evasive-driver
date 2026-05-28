# M1243 Paper-Route Capability-Separable Low-Regret Audit

## Summary

M1243 audits the M1242 source-constructor result:

```text
result_class: action_divergent_low_regret
accepted_separable_pairs: 0
```

Decision:

```text
low_regret_audit_select_short_sequence_lattice_smoke
```

The next step should not train, tune thresholds, or test actor history. It
should change one source-construction variable: replace the single first-action
lattice with a bounded short-sequence lattice.

## M1242 Evidence

M1242 final smoke:

```text
candidate_pair_count: 1356
matched_pair_count: 160
action_lattice_rows: 12000
action_rollouts: 24000
unique_matched_fault_family_pairs: 10
unique_matched_seeds: 20
accepted_separable_pairs: 0
best_actions_diverged_pairs: 3
low_regret_pairs: 160
result_class: action_divergent_low_regret
```

Guardrails held:

```text
actor_parameters_changed: false
labels_enter_actor_input: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
actor_input_contract_changed: false
```

Source diversity was repaired during M1242:

```text
per-seed cap: 8
per-fault-family-pair cap: 24
unique_matched_seeds: 20
unique_matched_fault_family_pairs: 10
```

So the zero accepted result should not be explained as seed collapse or
family-pair collapse.

## Distribution Audit

Best-action L2 distribution:

```text
min: 0.0
p50: 0.0
p90: 0.0
p99: 0.4000000060
max: 0.7211102843
```

Cross-regret A distribution:

```text
min: 0.0
p50: 0.0
p90: 0.0
p99: 0.0000004100
max: 0.0148353594
```

Cross-regret B distribution:

```text
min: 0.0
p50: 0.0
p90: 0.0
p99: 0.0000022220
max: 0.0015521341
```

Rejection reasons:

```text
best_actions_too_close: 157
insufficient_cross_regret: 2
best_candidate_not_viable: 1
```

Threshold audit:

```text
diverged >= 0.12: 3
both regrets >= 0.02: 0
A regret >= 0.02: 0
B regret >= 0.02: 0
```

This is not a threshold-near-miss. Lowering the cross-regret threshold enough
to accept rows would create weak source labels.

## Nonzero Divergence Rows

The strongest action divergence row:

```text
pair_id: 49
seed: 124206
family_pair: front_lateral_authority_drop->global_mu_drop
best_action_l2: 0.7211102843
cross_regret_A: 0.0148353594
cross_regret_B: 0.0000558759
best_A_success: false
best_B_success: false
rejection_reason: best_candidate_not_viable
```

The viable divergence rows:

```text
pair_id: 80
family_pair: front_lateral_authority_drop->global_mu_drop
best_action_l2: 0.4000000060
cross_regret_A: 0.0000004100
cross_regret_B: 0.0000022220
rejection_reason: insufficient_cross_regret

pair_id: 87
family_pair: rear_lateral_authority_drop->drive_authority_drop
best_action_l2: 0.4000000060
cross_regret_A: 0.0000024569
cross_regret_B: 0.0015521341
rejection_reason: insufficient_cross_regret
```

These rows show that hidden dynamics can change the best first action in a few
cases, but the closed-loop outcome penalty for using the other branch's first
action is tiny under the current rollout definition.

## Interpretation

M1242 rules out several easy explanations:

```text
not actor-input leakage: labels do not enter actor input
not actor mutation: checksum stable
not missing matched pairs: 160 matched pairs from 1356 candidates
not missing rollouts: 24000 candidate rollouts
not source collapse: 20 seeds and 10 family pairs
not threshold near-miss: no row has both cross regrets near 0.02
```

The likely bottleneck is that a one-step action override followed immediately
by unchanged policy continuation is too local. Many matched-current hidden
dynamics conditions either share the same best first action or can recover from
the other branch's first action within the next policy-controlled steps.

This does not prove the simulator cannot generate capability-separable cases.
It says the current source variable is weak:

```text
candidate object: one first action
continuation: frozen policy after that one action
criterion: terminal margin over 18 steps
```

The next bounded test should change only the candidate object.

## Selected Next Step

M1244 should implement and run a short-sequence lattice smoke.

Keep fixed:

```text
checkpoint
M1236 source config
cross-fault pairing
matched-current source criteria
seed/family-pair diversity caps
no training
no PPO
no promotion
actor input contract
```

Change one variable:

```text
candidate object: K-step action sequence instead of one first action
```

Recommended first smoke:

```text
sequence_length: 3
template_set: compact steer/brake pulse templates
max_pairs: 120
max_pairs_per_seed: 6
max_pairs_per_family_pair: 18
max_continuation_steps: 18 after the sequence
```

The same sequence candidates must be evaluated under both hidden-dynamics
conditions. Accepted separable rows remain diagnostic only.

## Why Not Other Next Steps

Do not train next:

```text
source separability is not established
```

Do not lower thresholds:

```text
max cross_regret_B is only 0.0015521341
```

Do not immediately change simulator fidelity:

```text
one-step source locality has not been ruled out
```

Do not broaden many variables at once:

```text
that would make the source repair hard to interpret
```

## Decision

```text
low_regret_audit_select_short_sequence_lattice_smoke
```

Next blocker:

```text
m1244-paper-route-capability-separable-short-sequence-lattice-smoke
```
