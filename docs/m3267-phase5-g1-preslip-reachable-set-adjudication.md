# M3267 Phase-5 G1 Pre-Slip Reachable-Set Adjudication

Date: 2026-07-10

## Decision

**Completed / inconclusive at the quick gate; full was not run.** The corrected
Chrono smoke produced finite and exactly replayable boundaries for all three
arms, with the grip arm clearing closer than the required-slide arm. The planar
required-slide arm did not produce a finite controlled-slide avoidance
boundary, so the frozen all-arm-completeness gate failed and no M3267 bounded
support or counterexample claim is admitted.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_prereg.json`
- Invalid r0 smoke retained for audit:
  `experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick_invalid_v0.json`
- Corrected r1 quick result:
  `experiments/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication_quick.json`
- Raw r1 rows:
  `runs/feasibility_audit/phase5_g1_preslip_reachable_set_adjudication/quick/`

## Protocol repair before adjudication

The first quick smoke was invalid for physical comparison. Chrono poses were
reported in the global curved-track frame but evaluated as if they were local
straight-road coordinates. It also allowed post-collision samples to enter the
slide-onset classifier. The r0 artifact is retained unchanged.

Revision r1, recorded before the corrected quick run, transformed every Chrono
pose into the scenario-initial lane frame, truncated classification at the
first collision/off-road/pass event, added deterministic early-steer/recenter
grip candidates, and required exact best-action replay. Claim thresholds,
cells, arm definitions, geometry, budgets, and seed streams were unchanged.

## Measured corrected quick boundaries

Smaller `D*` means the obstacle can be placed closer while the trajectory still
passes under the frozen mode, road, speed, and OBB constraints.

| backend | grip D* | required-slide D* | free D* | free mode | result |
|---|---:|---:|---:|---|---|
| planar, mu=0.60, 14 m/s | 13.3 m | not found | 12.9 m | grip-like | incomplete |
| Chrono, mu=0.48, 16 m/s | 18.8 m | 21.7 m | 16.1 m | grip-like | all arms finite |

For the Chrono quick cell, `D*_grip - D*_slide = -2.9 m`: the best found
required-slide trajectory needed 2.9 m more preview distance than the dedicated
grip trajectory. The unconstrained free search found an even closer grip-like
trajectory and no early-slide counterexample. Every corrected Chrono trajectory
started at local `(0,0,0)`, returned finite axle tire truth, and replayed with
maximum absolute error at or below `1e-12`.

The planar grip and free arms were finite, but no searched planar trajectory
simultaneously entered the required beta/rear-slip band before contact, stayed
below beta 0.70, cleared the OBB, remained on the 10 m road, and passed at speed
at least 4 m/s.

## Frozen gate table

| gate | result |
|---|---|
| Zhao et al. larger-control-set positive control retained | PASS |
| M3266 same-plant slide-entry positive control retained | PASS |
| corrected Chrono local frame | PASS |
| corrected Chrono exact replay | PASS |
| Chrono all-arm completeness | PASS |
| Chrono free consistency | PASS |
| planar all-arm completeness | **FAIL** |
| combined free consistency | **FAIL by incompleteness** |
| M3267 decision | `inconclusive` |

## Claim boundary

The Chrono quick row is feasibility pricing for a separately registered
high-fidelity adjudication. It is not a full-panel result. The planar search
failure does not prove that its controlled-slide feasible set is empty, and it
cannot be converted into dominance. M3267 changes no incumbent and makes no
universal vehicle, real-car, promotion, paper-readiness, or self-ID claim.

## Next admissible step

A new preregistration may use the healthy Chrono all-arm result to price a
Chrono-only full panel with fresh cells and seed streams. It must preserve the
contact plane, controlled-slide upper bound, free-oracle check, exact replay,
and 0.25 m boundary tolerance. Post-slip strict-recovery evidence remains a
separate experiment.
