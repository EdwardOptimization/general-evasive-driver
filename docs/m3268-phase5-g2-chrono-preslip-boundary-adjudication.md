# M3268 Phase-5 G2 Chrono Pre-Slip Boundary Adjudication

Date: 2026-07-10

## Decision

**Completed / inconclusive at quick; full was not run.** The fresh optimizer
seed reproduced finite grip and free boundaries but did not recover a finite
required-slide boundary. The frozen completeness gate therefore blocked full.

## Measured quick result

| arm | dedicated D* | pooled role |
|---|---:|---|
| grip | 18.6 m | grip |
| required slide | not found | none |
| free | 16.2 m | free and grip-like |

The local-frame, axle tire-truth, and exact-replay gates passed. M3265's
literature positive control and M3266's same-plant slide-entry control also
remained true. Dedicated and pooled all-arm completeness, free consistency,
worst-seed no-drift, and the primary comparison were not evaluable.

## Interpretation

M3267 found a valid required-slide Chrono boundary at the same mu and speed,
whereas M3268's fresh search seed did not. This is evidence that the current
small-budget CEM does not hit the narrow required-slide avoidance set reliably;
it is not evidence that the physical set is empty and not a pre-slip dominance
result.

## Next rule

One separately preregistered retry may freeze M3267's exactly replayed
required-slide action as a feasibility anchor before quick/full execution. It
must keep fresh optimizer streams, all M3268 gates, and the same 0.25 m rule.
If that anchor-based route still fails a full arm or seed gate, stop the
detailed-model boundary route rather than continue optimizer repairs.
