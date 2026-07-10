# M3270 Phase-5 H0 Fixed-Library Overlap Certificate

Date: 2026-07-10

## Decision

**Completed / finite-library overlap support admitted.** Canonical quick and
managed full passed every preregistered gate. Across the frozen 20-action
library, all 24 fresh full seeds had finite grip, required-slide, and free
boundaries; grip was better than required slide by 4.0-7.5 m on every seed.

This is an exact finite-library/finite-cell simulator certificate. It does not
prove dominance over the continuous Chrono control set and does not overwrite
M3269's inconclusive optimizer verdict.

## Frozen library

The preregistration retained every unique best physical segment sequence from
all Chrono searches in M3267 corrected quick and M3269 full, including actions
from failed source searches:

- 21 source action records;
- 20 unique float64 physical action sequences after exact hash deduplication;
- 3 failed-source required-slide actions retained;
- source artifact hashes, action hashes, cells, predicates, and seed streams
  frozen before quick;
- no optimization, action mutation, addition, or deletion during validation.

Every action was evaluated under grip, required-slide, and free predicates on
every validation seed.

## Full results

Smaller `D*` is better. Each range spans eight fresh validation seeds.

| mu | grip D* range (m) | required-slide D* range (m) | free D* range (m) | grip - slide range (m) | overlap |
|---:|---:|---:|---:|---:|---:|
| 0.48 | 15.6-15.7 | 21.7-22.7 | 15.6-15.7 | -7.1 to -6.0 | 8/8 |
| 0.60 | 13.8-13.9 | 19.1-21.3 | 13.8-13.9 | -7.5 to -5.2 | 8/8 |
| 0.90 | 11.7-11.8 | 15.7-16.2 | 11.7-11.8 | -4.5 to -4.0 | 8/8 |

All 24 best free trajectories were grip-like. No required-slide or controlled-
slide-like free trajectory beat the best grip trajectory by the 0.25 m frozen
counterexample threshold.

## Evidence health

| gate | result |
|---|---|
| source/action hashes frozen | PASS |
| expected classification rows | PASS, 480/480 |
| full overlap completeness | PASS, 24/24 seeds |
| grip no worse than slide +0.25 m | PASS, 24/24 seeds |
| free consistency | PASS, 24/24 seeds |
| controlled-slide free counterexample absent | PASS |
| local-frame origin | PASS, 480/480 rows |
| finite rear-tire truth | PASS, 480/480 rows |
| exact replay | PASS, 60/60, max error 0 |
| literature and same-plant slide-entry controls | PASS |

Primary artifact:
`experiments/feasibility_audit/phase5_h0_fixed_library_overlap_certificate.json`.
Raw action, replay, seed, and cell tables are under
`runs/feasibility_audit/phase5_h0_fixed_library_overlap_certificate/full/`.

## Permitted inference

Together with the bounded force-envelope theorem, M3270 supplies independent
numerical support on a detailed Chrono/TMeasy model for the selected overlap
domain: among every frozen source action, deliberate pre-obstacle sliding did
not enlarge the measured avoidance boundary and was strictly worse in all 24
fresh-seed comparisons.

Because `D*` is the minimum successful point on the common frozen 0.1 m
distance grid, each comparison also supplies a restricted grip-only witness at
its grip `D*`: a grip-classified action succeeds there and no required-slide
action in the same library succeeds there. This is strict boundary evidence on
the finite library and grid, not strict containment of the continuous Chrono
kernels.

The experiment does not enumerate the continuous control space, moving
obstacles, split-mu roads, vehicle variants, or real vehicles. The formal
continuous-set inclusion therefore comes from the stated theorem assumptions,
not from extrapolating this finite panel.

## Next gate

The pre-slip dual-evidence gate is now satisfied at its registered scope. A
separate post-slip panel may test strict recovery-set expansion, but it must use
correct physical zero-pedal semantics and compare nested control sets. No
incumbent, promotion, paper-readiness, or self-ID decision is made here.
