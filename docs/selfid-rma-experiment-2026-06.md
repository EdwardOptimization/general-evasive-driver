# Self-ID replaces the vehicle one-hot: history-inferred RMA recovers avoid without the label (2026-06-18)

## Why
The certified "strongest general driver" was general ONLY GIVEN a vehicle one-hot — a privileged label a human
never gets. A human FEELS THE CAR OUT (online system identification: throttle/steer response reveals mass + which
axle drives). This experiment replaces the one-hot with vehicle identity INFERRED FROM (obs,action) HISTORY, and
tests the two-regime VoI prediction: identity should have value exactly in AVOID (vehicle-specific), where the
one-hot mattered.

## Grounded constraints (the infra dig)
- On Chrono (the arbiter) the 3 vehicles are distinct multibody variants; mass + FWD/RWD drivetrain + TMeasy tyre +
  CG genuinely differ. The planar lf/lr/cf/cr are INERT for Chrono. On the GPU planar surrogate the "3 vehicles"
  differ ONLY in mass -> faithful self-ID MUST be measured on Chrono. So this whole experiment is Chrono-based.
- Deploy contract is obs72, no frame-stacking. The (obs,action) history window for phi / the GRU is maintained
  OUTSIDE the env (rollout loop + run_episode) -> the obs72 deployment contract is untouched.
- Teacher z = real extractable extrinsics [mass/2000, front_drive_share(FWD=1/RWD=0)] (mu EXCLUDED -- it is a road
  param, a leakage trap). sedan(0.725,1.0) uazbus(1.429,0.0) bmw(0.9,0.0): 3 distinct points.

## Four arms (selfid_models.py; avoid, 19 cells x 3 seeds x 3 vehicles on Chrono)
- A  one-hot   : the certified FiLMAvoidActorCritic (oracle-ID ceiling).
- B  no-ID     : FiLMZ with z==0 for all (no vehicle info; the floor).
- C1 RMA       : teacher FiLMZ(z=extrinsics) + adaptation phi((obs72,prev_action) window W=20)->z_hat regressed to z;
                 deploy with z_hat ONLY (NO label). Continuous z -> generalises to an unseen 4th vehicle.
- C2 GRU       : end-to-end GRU over (obs72, prev_action) -> implicit z -> gate + heads. No label, no teacher.

## phi IDENTIFIES the vehicle from interaction (mechanistic confirmation)
z_hat (inferred from a 20-step history window, mean per vehicle) vs true z:
  sedan  [0.767, 0.942] vs [0.725, 1.0]   -> mass + FWD recovered
  uazbus [1.374, 0.089] vs [1.429, 0.0]   -> heavy + RWD recovered
  bmw    [0.871, 0.143] vs [0.900, 0.0]   -> mid mass + RWD recovered
The (obs,action) history carries the vehicle's dynamic signature; phi extracts mass AND drivetrain. This is the
"feel the car out" signal, learned.

## RESULT (avoid success on Chrono)
| vehicle | A one-hot | B no-ID | C1 RMA (no label) | C2 GRU | C1 gap recovered |
|---|---|---|---|---|---|
| Sedan  | 1.000 | 0.018 | **1.000** | 0.368 | 100% |
| UAZBUS | 0.982 | 0.456 | **0.807** | 0.281 | 67% |
| BMW    | 1.000 | 0.298 | **0.596** | 0.228 | 42% |
| mean   | 0.994 | 0.257 | **0.801** | 0.292 | 74% |

## Verdict
- **Self-ID WORKS via RMA (C1).** History-inferred z_hat recovers ~74% of the B->A gap WITHOUT the privileged label
  (mean 0.257 -> 0.801); Sedan fully to the 1.0 ceiling. Directly supports the self-ID/VoI thesis: identity has
  value in avoid, and that value is RECOVERABLE from interaction (not a privileged-info artifact).
- **B (no-ID) collapses** (0.257, Sedan 0.018) -> vehicle identity genuinely matters in avoid (VoI confirmed).
- **C2 (end-to-end GRU) underperforms** (0.292, barely above the floor): learning ID + policy jointly from 324
  sequences is too hard; explicit RMA z-supervision is far more sample-efficient. C2 needs more data / tuning.
- **Residual gap is concentrated on BMW** (0.596). Likely cause: z=[mass, drive_share] is too coarse to separate
  BMW from UAZBUS (both RWD; differ in mass + tyre/CG, but tyre/CG are NOT in z). Clear lever: enrich z with more
  extrinsics (wheelbase/CG/tyre signature) and/or a richer phi.

## Next levers
1. Enrich z (add wheelbase/CG/tyre extrinsics) to close the BMW gap.
2. Leave-one-vehicle-out: train C1 on 2 vehicles, deploy on the 3rd via inferred z_hat -> the KILLER test the
   one-hot structurally cannot pass (no head/slot for an unseen vehicle).
3. C2: more sequences + GRU tuning, or a hybrid (GRU encoder regressed to z, RMA-style).

---

## Diagnostics (2026-06-18): the result is real but TWO confounds matter — read it as a matched ablation

### (1) The single z-conditioned avoid head is FRAGILELY z-conditioned
Deploying the C1 teacher with the TRUE z (oracle extrinsics, not phi-inferred):
| vehicle | C1 (phi-inferred z_hat) | C1 (TRUE z) |
|---|---|---|
| Sedan  | 1.000 | 0.368 |
| UAZBUS | 0.807 | 0.947 |
| BMW    | 0.596 | 0.175 |
| mean   | 0.801 | 0.497 |
The teacher does WORSE at the true z than at phi's slightly-off z_hat (phi differs from true z by only ~0.05-0.14).
=> the single z-FiLM avoid head has an ERRATIC z-response (small z change flips closed-loop success); the 0.801 rests
partly on phi's z_hat landing in good spots. z-jitter teacher (train z + N(0,0.12) per frame, the project's DR
philosophy on the conditioning var) made phi/true-z CONSISTENT but LOWER (phi 0.573 / truez 0.421) -- it smoothed the
response without lifting it. The single z-head is the architecture bottleneck (mirrors the S2 finding: shared head
fails, per-vehicle heads needed). Richer head conditioning (FiLM the head / soft-MoE) is the lever.

### (2) The A-vs-C comparison is UNFAIR (DAgger confound); the clean read is B-vs-C1
A (the certified capstone, 0.994) had **DAgger closed-loop correction + per-vehicle heads**. B/C1/C2 are **pure BC,
NO DAgger, single head**. The project already proved avoid is closed-loop-sensitive and DAgger is THE lever (low BC
MSE, closed-loop failures). So A's 0.994 is NOT a fair ceiling for a BC-only C1 -- much of the A->C gap is DAgger,
not the label.

**The clean, fair comparison is the matched ABLATION: B vs C1 -- identical FiLMZ single-head architecture, identical
BC-only training, differing ONLY in z:**
  B (no-ID, z=0): 0.257   ->   C1 (RMA, phi-inferred z from history): 0.801
This isolates the SELF-ID SIGNAL: replacing the vehicle label with history-inferred identity recovers avoid
0.257 -> 0.801 in a matched BC-only setting. The residual gap to A (0.994) is attributable to DAgger (closed-loop
correction), NOT to the label -- and DAgger can be added to C1 too.

### Honest headline
History-inferred self-ID (RMA) carries real, large value for cross-vehicle avoid (B 0.257 -> C1 0.801, matched
ablation; phi recovers mass+drivetrain from a 20-step window). The vehicle LABEL is replaceable by INTERACTION. Two
caveats keep it honest: (a) the single z-head is fragile -> needs richer head conditioning; (b) absolute level is
BC-capped -> add DAgger (the proven avoid lever) for an A-comparable, deployable self-ID driver. C2 (end-to-end GRU)
stays weak (0.292) -- needs more data or a hybrid (GRU encoder regressed to z).

---

## RMA + DAgger: the LABEL-FREE self-ID driver MATCHES the privileged one-hot ceiling (2026-06-18)

Both confounds fixed: (1) learned z-encoder ExtrinsicsEncoder(2->16), jointly BC-trained -> the FiLM conditions
ROBUSTLY (phi-z == true-z, the erratic single-2d-head fragility is gone); (2) DAgger (deploy phi-z_hat, relabel
student-visited states with the oracle, augment, retrain) -> closed-loop correction lifts the BC cap. _selfid_rma_full.py.

Progression (avoid, NO vehicle label = phi-inferred z_hat from a 20-step history window):
| stage | mean avoid | note |
|---|---|---|
| B no-ID (z=0, BC) | 0.257 | floor |
| C1 raw-2d-z (BC) | 0.801 | FRAGILE (phi 0.801 vs true-z 0.497) |
| learned-z (BC, no DAgger) | 0.415 | ROBUST (phi==true-z) but BC-capped |
| **learned-z + 1 DAgger round** | **0.970** | **A-comparable, NO label** |
| A one-hot + DAgger (privileged) | 0.994 | ceiling |

INDEPENDENT re-verification of the round-1 driver (selfid_rma_round1.pt) on the FULL 36-cell avoid set x5 seeds
(180 ep/vehicle/condition):
| vehicle | phi-z (NO label) | true-z |
|---|---|---|
| Sedan  | 0.917 (165/180) | 0.856 |
| UAZBUS | 0.994 (179/180) | 0.994 |
| BMW    | 1.000 (180/180) | 1.000 |
| mean   | **0.970** | 0.950 |

**VERDICT: the vehicle one-hot is REPLACEABLE.** Inferring the vehicle from (obs,action) interaction (phi) + closing
the loop (DAgger) yields a LABEL-FREE driver at 0.970 mean avoid -- essentially the privileged one-hot ceiling
(0.994) -- across 3 vehicles. phi-z ~= true-z confirms the identification is honest, not lucky. This is the working
realization of the user's thesis: a driver that FEELS THE CAR OUT instead of being told which car it is.

CAVEAT (honest): round 2 of DAgger COLLAPSED (phi-z 0.193) -- a bug (DAgger recovery FRAMES, which are unordered
visited states, were appended to the phi SEQUENCE pool where windows_from builds temporal windows -> garbage
windows polluted phi) compounded by DAgger over-augmentation. Round 1 is the selected best. FIX for the extensions:
(a) separate the teacher FRAME pool from the phi SEQUENCE pool (recovery frames -> frames only), (b) best-round
selection (like the capstone's worst-vehicle select). NEXT: leave-one-vehicle-out generalization (the test the
one-hot structurally cannot pass) + extend to drift (full-scenario self-ID driver).
