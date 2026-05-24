# M732 Source-Balanced Boundary Outcome Miner Audit

## Purpose

M732 audits M731 before launching another experiment.

The question is:

```text
After source balance and local boundary relocation are both fixed, what is the
next highest-leverage way to turn command-history action dependence into
closed-loop outcome evidence?
```

This audit is process-only:

```text
no actor training
no objective update
no PPO
no checkpoint promotion
no actor-input change
```

## Evidence Summary

M731 is a cleaner test than M722:

```text
source_candidate_rows: 512
source_unique_seeds: 237
source_unique_preferred_fault_families: 8
source_unique_fault_family_pairs: 30
source_max_seed_dominance: 0.017578
source_max_preferred_family_dominance: 0.126953
source_sentinel_fraction: 0.099609
sentinel_false_positive_rate: 0.0
normal_history_retention_pass: true
```

It also preserves strong action evidence:

```text
candidate_variant_count: 37248
temporal_action_critical_rows: 5881
```

Dominant variant:

```text
mismatch_zero_command_history:
  rows: 8192
  temporal action-critical: 5828
  temporal outcome-critical: 1
  first action distance mean: 0.020667
  margin gap max: 0.006462
```

But outcome evidence remains sparse:

```text
accepted_rows: 1
temporal_outcome_critical_rows: 1
outcome-positive target: >= 20
```

The singleton accepted row:

```text
seed: 72248
fault_family_pair: front_lateral_authority_drop->combined_fault
variant: mismatch_zero_command_history
normal_margin: 0.000389858
variant_margin: -0.001050173
first_action_distance_from_normal: 0.024997745
terminal_reason: collision
```

This row is diagnostic only.

## Supported Claims

M732 supports:

```text
1. M731 fixed the previous source selection artifact.

2. The actor has broad command-history action dependence under M728/M731
   source-balanced rows.

3. Local obstacle boundary relocation can find singleton outcome-sensitive
   rows, but not enough for a corpus.

4. Sentinel false positives and actor/input contract violations are not
   causing the result.
```

## Falsified Claims

M732 falsifies:

```text
1. M722 failed only because its source rows were concentrated.

2. Source-balanced one-step boundary mining is enough to produce an
   outcome-positive corpus.

3. Another same-style boundary miner is the obvious next step.

4. M731 justifies source export, actor update, PPO, or promotion.
```

M732 does not falsify:

```text
1. Sequence-level command-response interventions may produce larger outcome
   differences than one-step action mismatch.

2. Asymmetric/yaw-rich dynamics may be required for true tire blowout,
   split-mu, brake-pull, and half-shaft-loss failures.

3. The singleton accepted row can remain a diagnostic seed.
```

## Failure Taxonomy Summary

Primary:

```text
metric_artifact
```

Reason:

```text
Action-critical rows are abundant, but outcome-critical rows are still far
below the registered threshold.
```

Secondary:

```text
scenario_sampling_failure
```

Reason:

```text
The current one-step boundary relocation did not sample enough normal-viable,
history-sensitive outcome surfaces.
```

Not classified as:

```text
source_balance_blocked:
  source balance is now acceptable.

contract_violation:
  actor inputs were unchanged.

training_instability:
  no training occurred.
```

## Public Gate Overfit Risk

The risk is now high if the project keeps tuning local boundary grids:

```text
M731 already used broad source-balanced rows and a larger local obstacle grid,
yet it produced only one accepted row.
```

One more boundary miner could easily become grid chasing. A new branch should
change the evidence axis rather than only perturbing the same grid.

## Next Branch Decision

Decision:

```text
promote_to_next_branch: sequence_level_command_response_intervention
```

Rationale:

```text
M731 shows that one-step command-history action differences are often corrected
by the closed-loop rollout before terminal outcome changes. The next direct
test is to intervene over a short sequence window and ask whether persistent
wrong command-response history creates outcome differences.
```

This should be done before a dynamics-fidelity branch because it directly tests
the current blocker:

```text
action-to-outcome conversion under closed-loop feedback.
```

Dynamics fidelity remains an explicit fallback:

```text
if sequence-level interventions are still outcome-sparse, the next branch
should add true asymmetric/yaw-rich fault dynamics such as single-wheel grip
collapse, split-mu, brake pull, steering pull, or half-shaft torque loss.
```

## M733 Requirements

M733 should design a no-training sequence-level intervention runner from M728
or M731 source rows.

It should compare:

```text
normal closed-loop history
reset hidden at decision step
mismatch_zero_command_history for H steps
wrong command-response history persisted for H steps
delayed hidden persisted for H steps
pre-fault stale hidden persisted for H steps
```

Candidate horizons:

```text
H in {2, 4, 6, 8}
```

Acceptance gates:

```text
normal history remains viable
sequence intervention causes success drop or margin gap
sentinel false positives stay <= 0.05
source balance remains broad
actor parameters remain unchanged
no PPO and no promotion
```

The branch must keep action and outcome claims separate. If it remains
outcome-negative, the audit should promote to asymmetric/yaw-disturbance
dynamics-fidelity design.
