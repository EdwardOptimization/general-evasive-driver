# M612 Sequence Target Mining Design

## Purpose

M612 designs a short-horizon action-sequence target miner after M611 classified
the M610 blocker as first-action locality / myopia.

M610 showed:

```text
near-boundary rows + 80-step horizon + local first-action override
still produces zero accepted targets
```

Therefore M612 changes the target object from:

```text
one first action, then unchanged policy
```

to:

```text
a short bounded maneuver prefix, then unchanged policy
```

This milestone is design-only:

```text
no implementation
no training
no PPO
no checkpoint promotion
```

## Source Rows

M613 should start from:

```text
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
```

The M609 source set is only `17` rows, so any accepted sequences are diagnostic
only. They are not an optimizer-admissible corpus until a later milestone
improves source diversity or repeats the result on fresh boundary rows.

## Candidate Object

A sequence candidate should be:

```text
u_0, u_1, ..., u_{K-1}
```

where each `u_i` is a physical action:

```text
[steer, throttle, brake]
```

M613 should execute the full prefix open-loop, updating the recurrent hidden
state from observations at each step, then continue under the unchanged BC5660
policy.

Initial sequence lengths:

```text
K in {3, 5}
```

This keeps the search small while allowing a maneuver to have duration.

## Candidate Families

Do not start with an unconstrained Cartesian grid over all sequence actions.
That would explode combinatorially and produce off-manifold maneuvers.

Start with structured families around the base policy actions:

### Constant Delta

Apply one bounded delta for all prefix steps:

```text
u_i = clip(base_policy_action_i + delta)
```

Deltas:

```text
steer_delta    in {-0.08, -0.04, 0, +0.04, +0.08}
throttle_delta in {-0.06, 0, +0.03}
brake_delta    in {-0.08, -0.04, 0, +0.04, +0.08}
```

### Decay Pulse

Apply a strong first delta that decays to zero:

```text
scale = [1.0, 0.5, 0.25] for K=3
scale = [1.0, 0.7, 0.45, 0.25, 0.0] for K=5
```

### Brake Release Then Steer

For low-friction / saturated cases:

```text
step 0-1: reduce brake
step 1-K: add steer
```

### Steer Then Brake

For yaw initiation / mitigation cases:

```text
step 0-1: add steer
step 1-K: add brake
```

These are not rules for deployment. They are offline candidate generators used
to mine simulator-grounded target sequences.

## Trust Region

M613 should enforce hard trust-region checks:

```text
per_step_action_l2 <= 0.10
sequence_mean_l2 <= 0.08
sequence_max_l2 <= 0.10
max_delta_delta_l2 <= 0.08
```

The sequence should not be admitted if it relies on a single out-of-region
action spike. M610 showed the best first-action directions often lived outside
the trust region, so this rule is intentional.

## Rollout And Scoring

For each source row:

1. reconstruct the left snapshot;
2. compute baseline rollout from unchanged BC5660;
3. generate base policy actions for the prefix;
4. execute each candidate sequence prefix;
5. continue under unchanged BC5660;
6. record terminal reason, collision, off-road, spin, min margin, risk, and
   obstacle completion.

Initial continuation horizon:

```text
max_continuation_steps = 80
```

This aligns with M609 and M610.

Risk score should remain comparable to M606/M610:

```text
risk = collision_penalty + road_departure_penalty + spin_penalty - clipped_margin
```

## Acceptance

Hard reject:

```text
candidate_collision == true
candidate_off_road == true
candidate_spin_out == true
any per-step action trust-region violation
sequence trust-region violation
```

Utility accept:

```text
candidate avoids collision when baseline collides
or margin_improvement >= 0.02
or risk_improvement >= 0.05
```

M612 intentionally keeps M606/M610 thresholds unchanged. If sequence candidates
cannot pass these thresholds, the result should be recorded as another negative
rather than retroactively lowering the bar.

## Artifacts

M613 should write:

```text
runs/m613_sequence_target_miner/summary.json
runs/m613_sequence_target_miner/sequence_candidates.csv
runs/m613_sequence_target_miner/accepted_sequences.csv
runs/m613_sequence_target_miner/unaccepted_rows.csv
runs/m613_sequence_target_miner/selected_boundary_source_rows.csv
```

If accepted sequences exist, write:

```text
runs/m613_sequence_target_miner/sequence_target_corpus.npz
```

Initial NPZ fields:

```text
observation
normal_hidden
variant_hidden
target_action_sequence
normal_base_action_sequence
variant_base_action
weight
row_id
source_index
sequence_length
```

`variant_base_action` is still needed as a branch-preservation guard. M613 is
not allowed to make wrong-history branches safe by accident.

## Pass / Fail

M613 passes as infrastructure if it writes all candidate, accepted, unaccepted,
and summary artifacts without training or promotion.

Interpretation rules:

```text
accepted_sequences > 0:
  sequence target mining has signal, but diagnostic only

accepted_sequences == 0:
  local target mining is not enough; next branch should consider learned
  trajectory optimization, sequence-head shadow prediction, or source expansion
```

Either result must be documented before any optimizer step.

## Contract Checks

M613 must record:

```text
diagnostic_only: true
labels_enter_actor_input: false
actor_parameters_changed: false
ppo_used: false
promoted: false
optimizer_admission: false
```

## Decision

Decision:

```text
sequence_target_mining_design_admit_m613
```

Next:

```text
m613-sequence-target-miner-implementation
```
