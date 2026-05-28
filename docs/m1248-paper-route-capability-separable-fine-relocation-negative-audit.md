# M1248 Paper-Route Capability-Separable Fine Relocation Negative Audit

## Summary

M1248 audits the M1242-M1247 capability-separable source-construction branch.

Decision:

```text
local_relocation_source_exhausted_pivot_to_trajectory_proposal_source_design
```

Do not train on the current source. The current branch has repeatedly produced
valid infrastructure and useful diagnostics, but still has:

```text
accepted_separable_pairs: 0
```

This is not evidence against the overall General Evasive Driver objective. It
is evidence that the current source construction variable is too weak:

```text
matched-current source + fixed short-sequence lattice + local obstacle
relocation
```

The next source variable should be a branch-specific trajectory proposal/search
source, not another local relocation-grid expansion.

## Evidence Summary

| Milestone | Change | Matched rows | Rollouts | Accepted | Key finding |
| --- | --- | ---: | ---: | ---: | --- |
| M1242 | first-action capability-separable lattice | 160 | 24000 | 0 | source-diverse infrastructure passed, but result was action-divergent low-regret |
| M1244 | short-sequence lattice | 120 | 10320 | 0 | sequence actions increased action spread, but no branch-specific regret/viability signal |
| M1246 | coarse viability-band relocation | 48 | 4128 | 0 | relocation created 24 near-boundary rows and one near-positive nonviable two-sided regret row |
| M1247 | fine half-width/lateral relocation | 12 | 1032 | 0 | fine candidates worked, but viable rows stayed action-equivalent and action-divergent rows stayed nonviable |

The pattern is stable:

```text
near-boundary viable rows -> best_actions_too_close
action-divergent rows     -> best_candidate_not_viable
```

M1247 made this split explicit. The best two-sided regret case remained:

```text
pair_id: 5
seed: 124601
family_pair: global_mu_drop->brake_authority_drop
best_action_l2: 0.5049752593
cross_regret_A: 0.2107246264
cross_regret_B: 0.0201005052
pair_min_best_margin: -0.0048001855
rejection_reason: best_candidate_not_viable
```

The selected near-boundary viable case had:

```text
pair_id: 4
best_action_l2: 0.0
cross_regret_A: 0.0
cross_regret_B: 0.0
pair_min_best_margin: 0.0202010285
```

## Failure Classification

Primary failure type:

```text
scenario_sampling_failure
```

The source sampler is not yet producing states where hidden dynamics change the
best viable action. It is producing two adjacent but disconnected populations:

```text
1. viable, near-boundary, action-equivalent rows;
2. action-divergent, nonviable rows.
```

Not classified as:

```text
proof_washout: no trained actor update occurred
objective_overfit: no objective optimization occurred
behavior_regression: no promoted checkpoint was evaluated or changed
contract_violation: actor input contract stayed unchanged
private_holdout_contamination: private holdout was not used
```

## Supported Claims

M1248 supports these claims:

```text
the M1242-M1247 source-construction infrastructure is valid;
local relocation can target near-boundary viability;
current fixed short-sequence candidates are insufficient for accepted
capability-separable rows;
training remains blocked until a source-positive corpus exists.
```

M1248 does not support these claims:

```text
the policy has or lacks self-identification;
GRU history is or is not necessary;
the overall driver objective is infeasible;
the simulator is the limiting factor;
PPO should start.
```

## Why Not Continue Local Relocation

Another local relocation grid is low-value because M1246 and M1247 already
tested the intended repair:

```text
move source geometry into the viability band;
then fine-calibrate obstacle half-width and lateral offset.
```

The result did not fail because there were no fine candidates. M1247 produced:

```text
fine_relocation_candidates: 96
near_boundary_viability relocation candidates: 8
```

The result failed because the two required properties still did not coincide:

```text
viability and action separability remained separated.
```

Expanding the same public grid risks turning the branch into gate-chasing. A
new evidence variable is required.

## Next Source Variable

The next branch should test:

```text
condition-wise trajectory proposal/search
```

Instead of asking whether a fixed lattice around the actor's current action has
branch-specific regret, ask whether each hidden-dynamics condition has any
short-horizon feasible maneuver that differs from the other condition's best
maneuver.

Design sketch:

```text
for each matched-current hidden pair:
  search action sequences for condition A
  search action sequences for condition B
  keep top K viable proposals per condition
  evaluate cross-application A-proposal-on-B and B-proposal-on-A
  accept only if:
    both own-condition proposals are viable
    proposal vectors differ
    cross-application loses margin or success
```

This can be implemented as no-training random shooting, CEM/MPPI-style proposal
search, or a small deterministic proposal library. It remains source mining,
not deployment logic and not actor input.

## Decision

Stop:

```text
local relocation + fixed short-sequence lattice
```

Continue with:

```text
m1249-paper-route-capability-separable-trajectory-proposal-source-design
```

Guardrails remain unchanged:

```text
no training
no PPO
no promotion
no private holdout
no actor-input expansion
no self-identification claim
```
