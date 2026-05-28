# M1249 Paper-Route Capability-Separable Trajectory Proposal Source Design

## Summary

M1249 opens a new source-construction branch after M1248 stopped the local
relocation + fixed short-sequence lattice path.

Decision:

```text
trajectory_proposal_source_design_admit_bounded_smoke
```

This milestone does not train, promote, or change actor inputs. It designs a
no-training source miner that asks a sharper question:

```text
Can each hidden-dynamics branch find its own viable short-horizon maneuver, and
does applying the other branch's maneuver reduce margin or success?
```

This distinguishes two possibilities that M1242-M1247 could not separate:

```text
fixed lattice too weak
current source/state distribution not capability-separable under this model
```

## Why A New Source Variable

M1242-M1247 repeatedly found:

```text
accepted_separable_pairs: 0
```

The stable split is:

```text
near-boundary viable rows -> action-equivalent
action-divergent rows     -> nonviable
```

Expanding local obstacle relocation is now low-value. The next variable should
be the action-sequence proposal object itself.

## Candidate Generator

The M1250 smoke should add a new candidate mode:

```text
trajectory_proposal
```

For every matched-current hidden-dynamics pair:

1. compute the actor's deterministic action under condition A;
2. compute the actor's deterministic action under condition B;
3. generate short action sequences around A's base action;
4. generate short action sequences around B's base action;
5. add a small shared/common proposal set for comparability;
6. evaluate every proposal under both conditions.

Proposal metadata:

```text
candidate_id
candidate_origin: A | B | shared
sequence_length
candidate_vector
first_action
last_action
proposal_seed
proposal_template
```

The origin label is source metadata only. It must not enter the deployable actor
input.

## Initial Proposal Family

M1250 should start with deterministic no-training random shooting plus a small
structured library:

```text
sequence_length: 4
proposal_count_per_condition: 24
proposal_seed: fixed
steer_scale: 0.45
brake_scale: 0.45
throttle_scale: 0.25
```

Use proposal shapes that are plausible emergency controls:

```text
constant action
front-loaded steer pulse
front-loaded brake pulse
steer then brake
brake then steer
steer reversal / recovery
small throttle release or modulation
```

The proposal generator can sample deltas around each branch's base action, but
must clamp to the existing action bounds. It should avoid encoding hidden
fault labels into candidate generation; the only branch-specific information is
the branch's own observation/hidden-derived base action and closed-loop rollout
result.

## Acceptance Criteria

Use the existing separability semantics, but apply them to the proposal union:

```text
best_A = best proposal when rolled out in condition A
best_B = best proposal when rolled out in condition B
```

Accept a source row only if:

```text
best_A_success == true
best_B_success == true
margin_A_best_A >= 0.0
margin_B_best_B >= 0.0
normalized_l2(best_A_vector, best_B_vector) >= 0.12
cross_regret_A = margin_A_best_A - margin_A_using_best_B >= 0.02
cross_regret_B = margin_B_best_B - margin_B_using_best_A >= 0.02
```

M1250 may also report weaker diagnostics, but they must not be promoted to
accepted source evidence:

```text
one-sided regret
success drop in only one branch
near-positive nonviable rows
near-boundary action-equivalent rows
```

## Runtime Bound

M1250 is an infrastructure smoke, not a long search:

```text
seed_count <= 4
max_pairs <= 8
max_relocation_candidates <= 12
proposal_count_per_condition <= 24
sequence_length <= 4
max_continuation_steps <= 18
```

If this budget is too slow, the correct repair is to reduce pairs or proposal
count and record the runtime limit. Do not silently turn the smoke into a long
experiment.

## Artifacts

M1250 should write:

```text
summary.json
trajectory_proposals.csv
trajectory_proposal_rollouts.csv
accepted_separable_pairs.csv
rejected_pairs.csv
fault_family_pair_summary.csv
model_fidelity_limits.md
```

Summary fields should include:

```text
candidate_mode: trajectory_proposal
proposal_count_per_condition
proposal_seed
trajectory_proposals
trajectory_proposal_rollouts
accepted_separable_pairs
best_actions_diverged_pairs
low_regret_pairs
near_boundary_viability_pairs
actor_parameters_changed
labels_enter_actor_input
training_started
ppo_used
promoted
private_holdout_used
actor_input_contract_changed
```

## Guardrails

M1249/M1250 does not change the actor contract:

```text
no hidden parameters in actor input
no proposal labels in actor input
no oracle outcomes in actor input
no solver or search outputs in actor input
no training
no PPO
no promotion
no private holdout
no self-identification claim
```

If accepted proposal rows are found, the next step is compact source corpus
construction and exact replay sanity. It is still not a policy claim.

If no accepted proposal rows are found, the next audit should decide whether to
move to event-timing/source-state redesign or to a higher-fidelity dynamics
source, instead of expanding the same proposal budget indefinitely.

## Next

Admit:

```text
m1250-paper-route-capability-separable-trajectory-proposal-source-smoke
```
