# M1035 V4 Public Base Candidate B Guarded PPO Readiness Synthesis

## Purpose

M1035 is the required workflow synthesis for the Candidate B guarded PPO
readiness branch after M1025-M1034.

It does not run repair, PPO, training, private holdout, promotion, first replay,
or actor-input changes.

## Evidence Summary

M1023 promoted Candidate B as the current public-gate base:

```text
runs/m1016_v4_public_base_m1013_exact_candidate_preflight/checkpoints/m1013_lam0030_a050.pt
```

M1025 designed a guarded PPO smoke from Candidate B. M1026 ran it:

```text
PPO returncode: 0
training metrics finite: true
exact temporal retention: pass
fresh public / moderate-OOD / behavior: pass
public proof replay: fail on M267/M264 only
```

M1027 localized the M1026 proof washout:

```text
surface: M267/M264
row_id: 15
failure: wrong-history branch crosses from collision to success
normal branch: remains successful
```

M1028-M1029 designed and ran exact post-PPO repair with M297/M270, M293, and
M393 row15 conflict. The repair endpoints pass M297/M270 but fail M997 temporal
exact retention:

```text
M1029 exact M297/M270 candidates: 3/3
M997 temporal exact candidates: 0/3
```

M1030-M1031 tried temporal-safe interpolation/projection. Projection recovers
M997 temporal retention and M297/M270 exact no-regression:

```text
projected checkpoints: 39
temporal/exact-safe candidates: 16
replay-eligible candidates: 14
```

Projection can also retain M267/M264 row15 for several candidates, but no
candidate passes both first-replay surfaces:

```text
M267/M264: can pass 17/17 with row15 retained
M183/M170: 0/14 candidates pass
```

M1032 audits that failure. The closest miss is:

```text
candidate: raw_conflict_s40 alpha 0.05
M267/M264: 17/17 success drops
M183/M170: 16/17 success drops
failed row: 16
baseline normal_margin: +0.001316
candidate normal_margin: -0.000165
wrong_history_successes: 0/17
```

M1033 designs M183/M170 row16 as a hard active-set normal-trajectory retention
constraint. M1034 exports exact-loadable row16 normal-branch data:

```text
anchor rows: 57
observation shape: 57 x 72
hidden shape: 57 x 128
reference_action shape: 57 x 3
normal_success_all: true
wrong_history_success_any: false
```

## Supported Claims

The branch supports these claims:

```text
1. Candidate B is a valid public-gate base from M1023.
2. Smoke-scale guarded PPO from Candidate B can produce a finite proposal that
   preserves broad exact/generalization/behavior checks.
3. The raw PPO proposal is not promotable because it washes out M267/M264 row15.
4. Exact M297/M270 repair can recover current-family rejected-history objective
   feasibility.
5. M1029-style endpoint repair is too large unless temporal retention is made
   first-class.
6. Temporal-safe projection can recover M997 retention and M267/M264 row15 for
   some candidates.
7. The next hard constraint is M183/M170 row16 normal-branch retention, not
   wrong-history sensitivity loss.
8. M1034 now provides exact-loadable row16 normal trajectory data for the next
   active-set repair/projection attempt.
```

## Falsified Claims

The branch falsifies or blocks these claims:

```text
1. Raw M1026 PPO is acceptable as a new base.
2. M297/M270 exact repair alone is sufficient after PPO.
3. Temporal-safe projection alone is sufficient for first replay.
4. M267/M264 row15 is the only remaining proof surface after Candidate B PPO.
5. First-action-only retention is likely sufficient for M183/M170 row16.
6. Longer PPO should be run before active-set proof repair.
```

## Failure Taxonomy Summary

Observed failure classes:

| Milestone | Failure class | Meaning |
| --- | --- | --- |
| M1026 | `proof_washout` | M267/M264 row15 wrong-history branch becomes safe |
| M1029 | `proof_washout` | exact repair endpoints fail M997 temporal retention |
| M1031 | `proof_washout` | temporal/exact-safe projections fail first replay on M183/M170 |

No evidence in this branch shows:

```text
training_instability
contract_violation
private_holdout_contamination
behavior_regression
```

The recurring pattern is active-set proof washout: each repair fixes one proof
surface but exposes another low-slack proof surface.

## Public Gate Overfit Risk

Public-gate overfit risk is now moderate to high.

Reasons:

```text
1. The branch repeatedly uses fixed public proof rows.
2. Each repair/projection step is increasingly shaped by named rows:
   M267/M264 row15 and M183/M170 row16.
3. The current evidence is about retaining proof surfaces, not improving a
   broader scenario distribution.
```

Mitigation:

```text
The next branch may continue active-set repair only as a public proof-retention
engineering branch. It must not claim general driver improvement or paper-level
evidence. After a combined active-set candidate passes, a separate
generalization/promotion branch must refresh or broaden the surfaces.
```

## Next Branch Decision

Decision:

```text
promote_to_next_branch
```

New branch name:

```text
candidate_b_combined_active_set_repair
```

Rationale:

```text
The current branch has completed its job: it proved raw PPO is a useful but
unsafe proposal, localized the proof failures, and created exact-loadable data
for the missing active-set constraint. Continuing under the same guarded PPO
readiness branch would hide that the next work is no longer PPO readiness; it is
combined active-set repair/projection.
```

Next milestone:

```text
m1036-v4-public-base-candidate-b-combined-active-set-repair-design
```

M1036 should design a no-PPO combined active-set repair/projection using:

```text
M297 rejected-history preference
M270 outcome intervention
M293 current-family rejected-history trajectory anchor
M393 row15 conflict residual
M1034 M183/M170 row16 normal trajectory anchor
M997 temporal retention before replay
```

## Decision

```text
candidate_b_guarded_ppo_readiness_synthesis_promote_to_combined_active_set_repair
```
