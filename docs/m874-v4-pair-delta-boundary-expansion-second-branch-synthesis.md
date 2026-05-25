# M874 V4 Pair-Delta Boundary Expansion Second Branch Synthesis

## Purpose

M874 synthesizes the post-M863 continuation of the
`v4_pair_delta_boundary_expansion` branch before any further narrow
implementation, objective training, PPO, or promotion.

Covered milestones:

```text
M864-M873
```

M874 is synthesis-only:

```text
no replay
no actor update
no M761 residual-head update
no optimizer
no PPO
no checkpoint promotion
```

## Evidence Summary

M864 turned M860 generated brackets into useful boundary rows:

```text
combined boundary-new-to-M844 rows: 59
combined source groups: 27
combined seeds: 5
combined fault families: 9
primary pairability projections: 365
```

M865/M866 correctly separated pairability from outcome evidence and admitted a
limited pair-delta refresh.

M867 converted pairability into real pair-delta outcome rows:

```text
pair_delta_sequence_rows: 1416
accepted_pair_delta_rows: 234
pair_delta_success_flip_rows: 97
pair_delta_collision_flip_rows: 97
```

But accepted coverage was concentrated:

```text
accepted left seeds: 78058 and 78050
balanced_pair_delta_rows: 32
balanced_unique_left_seed_count: 2
balanced_max_direction_dominance: 0.75
balanced_max_axis_pair_dominance: 0.96875
```

M868/M869 routed to targeted accepted-coverage expansion.

M870 implemented targeted retarget replay over missing seeds:

```text
target_weak_seed_rows: 24
retarget_candidate_rows: 96
pair_delta_sequence_rows: 1728
new_accepted_pair_delta_rows: 0
```

M871 audited why M870 failed: the retarget grid missed the accepted normal
window:

```text
normal_ok rows: 0 / 1728
normal_margin < 0.0: 1152
normal_margin > 0.03: 576
```

M872 designed a boundary-preserving two-stage refresh.

M873 implemented that design and passed the registered no-training coverage
gates:

```text
normal_boundary_candidate_rows: 48
normal_boundary_unique_left_seed_count: 3
normal_boundary_unique_retarget_axis_count: 3
pair_delta_sequence_rows: 864
new_accepted_pair_delta_rows: 39
accepted_pair_delta_rows: 273
balanced_pair_delta_rows: 56
balanced_unique_left_seed_count: 4
balanced_unique_left_source_group_count: 11
balanced_unique_left_fault_family_count: 8
balanced_unique_fault_family_pair_count: 27
balanced_unique_direction_count: 2
balanced_unique_axis_pair_count: 2
balanced_max_left_seed_dominance: 0.35714285714285715
balanced_max_direction_dominance: 0.5178571428571429
balanced_max_axis_pair_dominance: 0.6607142857142857
```

All implementation milestones preserved frozen actor and M761 residual-head
checksums. No training, PPO, or promotion occurred.

## Supported Claims

The branch now supports these claims:

```text
M864-M873 can construct no-training pair-delta outcome evidence from generated
boundary rows.

Pairability projection alone is insufficient; actual sequence replay is needed
and was implemented.

The initial M867 accepted surface was real but source-limited.

M870 demonstrated that coarse missing-seed retargeting can create outcome
sensitivity but miss the accepted normal-window contract.

M873 fixed that specific normal-window miss by separating normal-boundary
search from pair-delta sequence replay.

The combined M873 accepted corpus is materially more source-diverse than M867:
56 balanced rows across 4 left seeds, 11 source groups, 8 fault families, and
27 fault pairs.
```

## Falsified Claims

The branch falsifies or weakens these claims:

```text
M864 pairability projections are enough for objective training.

M867 accepted rows are already source-diverse enough.

Coarse obstacle retargeting can be used directly before pair-delta replay.

High margin deltas on already-colliding normal branches can count as primary
pair-delta evidence.

The missing-seed gap is fully solved.
```

Important caveat:

```text
M873 produced new accepted rows for 78048 and 78057, but not for 78055.
78055 has accepted normal-boundary candidates but zero new accepted pair-delta
rows.
```

## Failure Taxonomy Summary

`scenario_sampling_failure`:

```text
Dominant failure type through M867-M871. It was reduced by M873 but not fully
eliminated because 78055 remains without new accepted pair-delta rows.
```

`metric_artifact`:

```text
Controlled by separating pairability, normal-boundary rows, pair-delta sequence
rows, component controls, and accepted primary evidence. M871 explicitly
rejected colliding-normal high-delta rows as non-primary evidence.
```

`contract_violation`:

```text
Not observed. Actor and residual-head checksums stayed unchanged throughout
the no-training branch continuation.
```

## Public Gate Overfit Risk

Overfit risk is moderate:

```text
The branch used public generated-boundary and pair-delta surfaces repeatedly.
M873's result is positive, but it is still a no-training corpus construction
result on public surfaces, not a learned driver claim.
```

Risk controls:

```text
Keep objective training blocked until an objective-readiness audit.
Preserve source-aware train/eval/holdout splits written by M873.
Do not tune an actor directly against the same public rows without retention and
holdout controls.
Do not claim paper-level generalization from this corpus alone.
```

## Next Branch Decision

The current data-construction branch should close.

Decision:

```text
promote_to_next_branch
```

New branch:

```text
v4_pair_delta_objective_readiness
```

Next milestone:

```text
m875-v4-pair-delta-objective-readiness-audit
```

M875 should audit whether M873's corpus is suitable to design an objective
training or exact repair objective. It should check:

```text
1. duplicate pressure from original delta=0 rows;
2. whether M873 new accepted rows add enough unique closed-loop information
   beyond M867;
3. whether the 78055 caveat blocks objective design or can be carried as a
   documented limitation;
4. whether source-aware splits are sufficient for objective sanity;
5. what exact no-training objective-readiness gates must pass before any actor
   update.
```

PPO and promotion remain blocked.
