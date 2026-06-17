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
