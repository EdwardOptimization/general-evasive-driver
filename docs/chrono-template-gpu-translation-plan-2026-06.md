# Chrono template framework → batched-GPU translation — plan (2026-06-17)

The faithful, cross-vehicle path (replaces the leaky per-vehicle reduced-order rewrite). User's
insight: don't rewrite per vehicle; translate Chrono's TEMPLATE framework once → any vehicle = config.

## How Chrono unifies vehicles (the mechanism)
ChWheeledVehicle = vector<ChAxle> + steerings + driveline + chassis + powertrain. Each ChAxle holds a
ChSuspension* TEMPLATE SLOT. The concrete vehicle classes (Sedan_DoubleWishbone, Sedan_TMeasyTire,
Sedan_Driveline2WD, ...) are PURE PARAMETER CONTAINERS (static-const hardpoints/masses/coeffs + getters,
ZERO physics); the physics is in the shared base templates (ChDoubleWishbone, ChTMeasyTire,
ChShaftsDriveline2WD, ChRackPinion). ~18 vehicles in chrono_models, all thin param subclasses over the
same templates. So: a vehicle IS a config (template choice + params). Generality is by construction.

Template categories (the config schema): Suspension {DoubleWishbone, MultiLink, MacPherson, SolidAxle,
DoubleWishboneReduced, ...}; Steering {RackPinion, PitmanArm}; Driveline {ShaftsDriveline2WD/4WD,
Simple}; Tire {TMeasy, TMsimple, Pac02, Rigid, Fiala}; Brake {Simple, Shafts}; Engine {SimpleMap,
Shafts}; Transmission {AutoSimpleMap, ManualShafts}; Chassis {Rigid}. Sedan = DoubleWishbone front +
MultiLink rear + TMeasy + ShaftsDriveline2WD (FWD) + RackPinion + EngineSimpleMap + AutoTransSimpleMap.

## Sedan multibody size (full linkage)
~17 ChBody (chassis + 4 bodies/side × 2 × 2 axles) = ~102 maximal DOF; ~100-105 bilateral constraints
(DoubleWishbone 23/side incl. spindle revolute + axle-shaft coupling); net ~10-15 true DOF (chassis 6 +
4 suspension travel + 4 wheel-spin + steer 1). ChDoubleWishboneReduced (2 bodies/side + distance
constraints) is a faithful lower-DOF middle tier. No fully-kinematic suspension template SHIPS (author it).

## Per-step solve
Index-3 DAE KKT [M Cqᵀ; Cq -E][a;λ]=[f;-b]. NSC (default) = iterative cone-complementarity (PSOR/APGD,
BRANCHY — avoid). SMC = penalty contact → single saddle-point LINEAR solve (batchable, torch.linalg.solve
over [N,d,d]). Integrator = half-implicit linearized Euler (1 linear solve/step). For GPU: pick SMC +
half-implicit Euler.

## GPU translation breakdown
- EASY (elementwise, parallel): TMeasy tire force (have curves; +Dahl bristle 2 states/wheel), engine
  map, brake, spring/shock ForceFunctors.
- CRUX: the constrained multibody suspension EOM + batched saddle-point solve + per-joint-type Jacobians.
- BRANCHY (→ masked branchless): gear FSM (masked per-gear ratio), NSC cone (avoid→SMC), diff clutch/lock,
  tire contact on/off, brake lock. 1D driveline = small linear KKT blocks (open diff = 3-shaft linear
  constraint), easy.

## Effort tiers
- (a) KINEMATIC-suspension faithful template port: chassis 6-DOF + 4 corners (vertical travel + camber/
  toe/track/Fz-vs-travel LOOKUP derived from the Chrono linkage hardpoints) + TMeasy + driveline +
  engine/trans gear-FSM, branchless, NEARLY EXPLICIT (no constraint solve), differentiable. Cross-vehicle
  general (lookups are per-template config). ~1.5-3 weeks. **RECOMMENDED.**
- (b) FULL-LINKAGE multibody port: batched index-3 DAE + joint Jacobians + saddle-point solve +
  stabilization. Exact. ~6-12 weeks (reduced-linkage intermediate ~4-6). Reserve for articulation cases.

## Recommendation
Tier (a). It is STRICTLY more faithful than the planar reduced-order rewrite (adds chassis roll/pitch +
per-corner suspension travel = the residual cornering/load-transfer gap that left avoid vx at 0.90), is
cross-vehicle general by construction, and stays GPU-batchable + differentiable. First concrete step:
derive the per-corner kinematic suspension lookups (camber/toe/track/Fz vs travel) from the Chrono Sedan
hardpoints (Sedan_DoubleWishbone getLocation + the ChDoubleWishbone kinematics), via pychrono in the
chrono conda env, validated against a Chrono ramp/step-steer.

Source anchors: ChWheeledVehicle.h:48,268-270; ChAxle.h:84-88; ChSuspension.h:167-170; ChDoubleWishbone.h:
256-271; ChDoubleWishboneReduced.h:161-167; Sedan_*.h; ChSystemDescriptor.h:34-49; ChTimestepper.h:34-47.

---

## Tier-a STEP 1 DONE (2026-06-17): per-corner kinematic suspension lookups extracted from Chrono

`extract_chrono_suspension_kinematics.py` -> `chrono_suspension_kin.npz` (92 arrays, per-corner FL/FR/RL/RR:
z_grid ±0.070m × 23pts, camber, toe, track_shift, wheel_xyz, spring_force, spring_length, tire_normal_force,
static_*; + steering Ackermann). Read from the REAL Chrono DoubleWishbone(front)/MultiLink(rear)/RackPinion
linkage solved every step (ChSuspensionTestRig ships but its fixed-chassis post rig can't read wheel rate +
segfaults on lone non-front axle -> used a free-vehicle ramped chassis-load sweep; verified the JSON vehicle
matches C++ veh.Sedan() to 1e-4m). Measured sanity (re-spot-checked): front camber gain 2.25°/0.1m, rear
1.20°; front wheel rate 42.8 kN/m, rear 18.8 kN/m; track shift front ±34mm (wishbone) / rear ±3mm (multilink);
Ackermann (inner steers ~2.3° more). Honest gaps: wheel rate is SPRING-only (combine with the saved
spring_force curve + TMeasy vertical tire stiffness in series, not a lumped rate); DAMPER/shock NOT extracted
(spring path only — add if the corner needs vertical damping); extrapolation beyond ±70mm unsupported.

This is the artifact that (a) closes the planar model's roll/pitch + per-corner load-transfer gap and (b) is
per-template (same extraction = any vehicle's suspension). Next Tier-a steps: chassis 6-DOF + 4 corners using
these lookups + TMeasy + driveline + masked gear-FSM -> batched branchless GPU; validate vs Chrono ramp/step-steer.

---

## Tier-a model BUILT + gated (2026-06-17): falsifies roll/pitch hypothesis; not faithful enough on drift

gpu_vehicle_tier_a.py — chassis 6-DOF + 4 kinematic corners (measured Chrono damper: front shock 10000,
rear 15000 N·s/m → ζ_f≈0.69/ζ_r≈0.30; the lookups + TMeasy + FWD powertrain). Built, batched, 5 tests pass,
2 real bugs fixed (Ackermann sign, front diff-cap asymmetry). Gate (independently re-verified):

| metric | planar pwr | Tier-a |
|---|---:|---:|
| avoid vx_rmse | 0.897 | 0.903 (NO change) |
| avoid vy_rmse | 0.126 | 0.105 (slight ↑) |
| drift β@24 p90 | 0.0283 (PASS) | **0.0756 (FAIL)** |

Two clean findings:
1. **The avoid vx-0.90 gap is NOT roll/pitch — it's LONGITUDINAL DECELERATION** (the model coasts/brakes
   too slowly vs Chrono; the vx error profile is identical to planar at every step). Load transfer can't
   touch it; the fix is the brake/engine-brake/coast deceleration model (longitudinal), unaffected by chassis DOF.
2. **The kinematic-reduced suspension is NOT faithful enough for the drift transient.** The faithful dynamic
   load transfer through the concave TMeasy Fy(Fz) over-reduces rear grip → rear over-rotates → β diverges
   (0.076). The kinematic corners MISS the real anti-roll-bar / roll-center geometry, so they over-predict
   the transient roll transfer. The planar model matches Chrono drift BETTER (0.028) — partly by a
   compensating quasi-static error, but empirically closer. Full faithfulness here needs Tier-b (full
   linkage incl. anti-roll), the 6-12wk build — NOT the kinematic reduction.

**STRATEGIC REFRAME (important):** the DO-BOTH driver does NOT depend on surrogate fidelity at all — it is
solved ON CHRONO via distillation + DAgger (drift 1.0 + avoid 0.900→1.0), where the surrogate's only role is
producing the DRIFT EXPERT (whose drift transfers to Chrono 1.0 from the cheap PLANAR model). So Tier-a is
NOT on the do-both critical path, and the kinematic Tier-a isn't faithful enough anyway. For CROSS-VEHICLE:
use the cheap planar model per-vehicle (template params) to train per-vehicle drift experts + the avoid
oracle + distill/DAgger on Chrono; test per-vehicle TRANSFER. Reserve Tier-b (full linkage) only if a
vehicle's planar drift-expert fails to transfer. The "GPU rewrite" value is the 2400× SPEED (planar delivers
it), not chasing kinematic-Tier-a fidelity.
