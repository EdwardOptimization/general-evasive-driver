# M3218 S4-HF-lite Backend Inventory Preflight

Status: completed. This is a zero-rollout infrastructure preflight for the S4-HF-lite route; it is not a pricing run, not a driver-performance result, and not RL evidence.

## Verdict

- Direct S4-HF-lite pricing admitted now: **false**.
- Reason: The repository worker/backend still hard-code veh.Sedan() with TireModelType_TMEASY and expose no variant selector; scenario lf/lr/iz/cf/cr are carried but not mapped into Chrono dynamics.
- Next admitted milestone: M3219 Chrono variant-selector smoke before any S4-HF-lite pricing run.

## What Chrono Provides

- Chrono vehicle data path: `/home/quyaonan/miniforge3/envs/chrono/share/chrono/data/vehicle`.
- Vehicle JSON files visible: 484; vehicle module classes visible: 623.
- Passenger-like data candidates found: `Nissan_Patrol`, `VW_microbus`, `audi`, `gclass`, `sedan`, `uaz`
- Tire model attributes visible: `FialaTire`, `Pac02Tire`, `Pac89Tire`, `RigidTire`, `TMeasyTire`, `TireModelType_ANCF`, `TireModelType_FEA`, `TireModelType_FIALA`, `TireModelType_PAC02`, `TireModelType_PAC89`, `TireModelType_REISSNER`, `TireModelType_RIGID`, `TireModelType_RIGID_MESH`, `TireModelType_TMEASY`, `TireModelType_TMSIMPLE`

## What Is Actually Wired

- Backend id: `chrono_sedan_tmeasy_hf_backend`.
- Backend source: `src/autodrift/chrono_vehicle_backend.py`; worker: `scripts/feasibility_audit/chrono_backend_worker.py`.
- Hard-coded `veh.Sedan()`: True.
- Hard-coded `TireModelType_TMEASY`: True.
- Runtime vehicle/tire variant selector present: False.
- Scenario carries `lf/lr/iz/cf/cr`: True, but they are not mapped into Chrono dynamics.

| channel | current status | note |
|---|---|---|
| `mu` | `mapped` | Scenario mu is mapped to Chrono FlatTerrain friction, including friction-step replacement. |
| `mass` | `partial` | Total mass is matched through a chassis-mass override; CG, axle split, and inertia remain Sedan. |
| `drive_scale/brake_scale` | `partial` | Mapped as throttle/brake command scaling and clipped at 1.0, so >1 scales saturate. |
| `drive_tau/steer_tau/max_steer_rate` | `mapped_control_layer` | AutoDrift-style first-order/rate actuator filter is applied before Chrono driver inputs. |
| `lf/lr/cg_shift/axle_load_split` | `not_mapped` | Scenario carries lf/lr but current backend leaves Sedan geometry and load split unchanged. |
| `iz/inertia_scale` | `not_mapped` | Scenario carries iz but current backend does not alter Chrono inertia tensors. |
| `cf/cr/tire_curve_family` | `not_mapped` | Scenario carries cf/cr but current backend always uses Sedan TMeasy tire data. |
| `vehicle_model` | `not_mapped` | The backend constructs veh.Sedan() unconditionally and the worker has no variant option. |

## Minimal Next Connectors

- Add an explicit Chrono backend variant selector (vehicle model + tire model or JSON fixture).
- Expose reset-time backend_info with selected model, tire model, mass, max steer, wheelbase, chassis inertia, and tire family.
- Map or deliberately bracket lateral channels: lf/lr/CG placement, Iz/inertia, axle load split, and tire curve family.
- Run a no-policy reset/step smoke for at least Sedan nominal plus two passenger-like variants before S4 pricing.
- Freeze S4-HF-lite seed streams and report as pricing only; no RL, no driver-performance claim.

## Claim Boundary

Allowed: Chrono resource inventory, current backend wiring audit, and admission of the next connector milestone.

Rejected explicitly: driver-performance, high-fidelity sufficiency, S4/C5 pricing result, RL evidence, validation/ranking/promotion, paper evidence, or any mutation of the deployed v4 incumbent.

## Artifacts

- JSON: `experiments/feasibility_audit/s4_hf_lite_backend_inventory.json`
- Script: `scripts/feasibility_audit/s4_hf_lite_backend_inventory.py`
