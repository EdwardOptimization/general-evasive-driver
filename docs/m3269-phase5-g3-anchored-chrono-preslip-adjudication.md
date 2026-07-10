# M3269 Phase-5 G3 Anchored Chrono Pre-Slip Adjudication

Date: 2026-07-10

## Decision

**Completed / full result inconclusive; the detailed-model optimizer route is
closed.** Canonical quick passed every gate. Full produced no slide-advantage
counterexample and two nonempty cells favored grip by large margins, but the
required-slide arm was incomplete at low friction and for one high-friction
seed. The frozen full completeness rule therefore rejects bounded empirical
support.

## Frozen anchor

M3267's exactly replayed required-slide trajectory was frozen before M3269 by:

- source seed `1515484633` and source `D*=21.7 m`;
- shape `[7,3]`;
- float64 SHA256
  `20f2be985795d97f6507eca83ca046535ca6fcabca27247dadc970c5f2952281`;
- structured-candidate index 4, evaluated at the preregistered 23 m joint
  search distance.

The anchor used the same action, actuator, mode, road, geometry, and stability
constraints as every other trajectory.

## Full boundary results

Smaller `D*` is better. Brackets show the two dedicated optimizer seeds.

| mu | grip D* | required-slide D* | free D* | pooled grip/slide | verdict |
|---:|---:|---:|---:|---:|---|
| 0.35 | 18.1 `[18.1,18.7]` | not found `[null,null]` | 18.6 `[18.8,18.6]` | 18.1 / null | incomplete |
| 0.60 | 14.0 `[14.4,14.0]` | 20.7 `[20.9,20.7]` | 13.9 `[14.9,13.9]` | 13.9 / 20.7 | grip better by 6.8 m |
| 0.90 | 12.0 `[12.0,12.1]` | 15.7 `[null,15.7]` | 11.8 `[11.9,11.8]` | 11.8 / 15.7 | grip better by 3.9 m; seed incomplete |

Every best free trajectory was grip-like. No required-slide or early-slide free
trajectory beat grip by the 0.25 m counterexample threshold. All local-frame,
axle tire-truth, and exact-replay checks passed with replay error 0.

## Gate disposition

| gate | result |
|---|---|
| canonical quick | PASS |
| literature and same-plant slide-entry controls | PASS |
| local frame, tire truth, exact replay | PASS |
| no observed slide advantage | PASS on finite comparisons |
| no free-slide counterexample | PASS |
| mu=0.60 all arms and seeds | PASS |
| mu=0.35 required-slide completeness | **FAIL** |
| mu=0.90 every-seed completeness | **FAIL** |
| frozen full decision | `inconclusive` |

## Permitted inference

The detailed model is consistent with the force-envelope theorem wherever a
matched controlled-slide boundary was found, and the two fully/partly nonempty
full cells favored grip by 3.9-6.8 m. No drift-only witness was found.

The experiment does **not** certify the required-slide set as empty at mu=0.35
and does not pass the preregistered finite-domain dual-support rule. Therefore
the paper may state the bounded force-envelope theorem and report supporting
but incomplete numerical evidence; it may not state that experiment and theory
jointly prove detailed-vehicle dominance.

## Stop consequence

No further local optimizer repair is admitted. The post-slip strict-recovery
panel and paper claim promotion remain blocked by the failed pre-slip evidence
gate. The incumbent is unchanged and no self-ID claim is made.
