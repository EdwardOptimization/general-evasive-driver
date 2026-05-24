# M608 Boundary-Conditioned Grounded Source Design

## Purpose

M608 designs the source-selection step needed after M607.

M607 found that the first M606 target miner failed mainly because selected
source rows were not close enough to a behaviorally meaningful short-horizon
boundary. M608 therefore changes the next question from:

```text
Can every belief-only gap become an action target?
```

to:

```text
Which belief-only gaps are near enough to collision / margin / risk boundaries
to justify grounded local action target search?
```

This milestone is design-only:

```text
no training
no PPO
no checkpoint promotion
no target relabeling
```

## Source Pool

M609 should start from the full M604 coupling table, not just the M606 top-23
subset:

```text
runs/m604_guarded_capability_action_coupling_evaluator/coupling_rows.csv
```

Initial supported variants:

```text
wrong_matched_history
delayed_history
```

Reason: these variants can be reconstructed deterministically from left/right
or delayed rollout snapshots using the current outcome helpers. `shuffled`
history remains useful as a belief diagnostic, but it should not be admitted to
the first boundary-conditioned source miner unless its hidden-state provenance
is made deterministic and auditable.

Source filter before rollout:

```text
candidate_for_grounding == true
variant in {wrong_matched_history, delayed_history}
capability_z_distance >= 0.10
action_distance remains below the M604 action-coupling threshold
```

## Baseline Boundary Screen

For each source row, M609 should reconstruct the left snapshot and run a
normal-branch baseline continuation under unchanged BC5660.

Use a longer screen than M606:

```text
baseline_continuation_steps = 80
```

M606 used `40` steps. M608 does not interpret the 40-step result as wrong, but
the audit showed many rows were far from short-horizon boundary; a longer
screen is a better source selector before spending action-grid rollouts.

Record at minimum:

```text
baseline_success
baseline_collision
baseline_off_road
baseline_spin_out
baseline_terminal_reason
baseline_min_clearance_margin
baseline_risk_score
obstacle_completed
```

Admit boundary candidates if any of the following holds:

```text
baseline_collision == true
baseline_min_clearance_margin <= 0.50
baseline_risk_score >= risk_quantile_75_of_source_pool
```

Hard reject:

```text
baseline_off_road == true
baseline_spin_out == true
invalid or missing reconstructed snapshot
```

The `0.50` margin window is intentionally looser than the M607 diagnostic
`<= 0.1` count. M607 found only `4 / 23` selected rows at or below `0.5`, so
M609 needs to scan the broader source pool before tightening.

## Boundary Score

M609 should rank admitted rows with:

```text
boundary_score =
  capability_z_distance
  * (1 + max(0, 0.5 - baseline_margin))
  * (1 + normalized_baseline_risk)
  / sqrt(rows_from_same_physical_pair_variant_target)
```

This keeps capability movement in the score but makes boundary proximity the
gate. Belief movement alone remains insufficient.

## Diversity Requirements

M609 is still an infrastructure/source-mining milestone, not a training result.
It passes if it produces a usable boundary source set with enough diversity for
a second grounded target miner.

Desired admission thresholds:

```text
accepted boundary source rows >= 24
unique physical pairs >= 8
unique left seeds >= 8
surfaces >= 2 when available
variants >= 2 when available
targets >= 2
max single physical-pair dominance <= 25%
```

If these thresholds fail, M609 should write the rejected/far rows and classify
the blocker rather than silently relaxing the criteria.

## Artifacts

M609 should write:

```text
runs/m609_boundary_conditioned_source_miner/summary.json
runs/m609_boundary_conditioned_source_miner/source_rollouts.csv
runs/m609_boundary_conditioned_source_miner/boundary_source_rows.csv
runs/m609_boundary_conditioned_source_miner/rejected_far_rows.csv
```

No target corpus is produced in M609. The output is a source set for a later
target-search milestone.

## Next Target Search

Only if M609 finds enough source-diverse boundary rows should the project rerun
grounded local action search.

The follow-up target miner should:

```text
read boundary_source_rows.csv
reuse M606 action-grid logging format
start with the same max_action_l2 = 0.10
keep M606 acceptance thresholds unchanged initially
write unaccepted rows even if no targets pass
```

If a second run still accepts zero targets, then the likely blocker is no longer
source-row boundary distance; it becomes first-action locality or the need for
short sequence targets.

## Branch Preservation

The future target miner must keep the M605 branch-preservation rule:

```text
normal hidden branch may move only toward simulator-grounded targets
variant branch must be anchored unless it has its own grounded target
belief-only gaps are never direct action-separation labels
```

This protects against the previous failure mode where repairing the normal
branch accidentally made wrong-history behavior safe.

## Pass / Fail

M608 passes if this design is recorded and validated before M609 implementation.

M609 should pass only if it writes all source-screen artifacts and either:

```text
finds a source-diverse boundary set
or clearly classifies why the M604 source pool is not boundary-actionable
```

Training, PPO, and checkpoint promotion remain blocked.

## Decision

Decision:

```text
boundary_conditioned_grounded_source_design_admit_m609
```

Next:

```text
m609-boundary-conditioned-source-miner-implementation
```
