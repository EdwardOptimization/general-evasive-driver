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
