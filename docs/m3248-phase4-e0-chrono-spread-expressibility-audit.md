# M3248 Phase-4 E0 Chrono Spread Expressibility Audit

Status: completed. This is a zero-training Phase-4 E0 audit; it freezes
the Chrono vehicle-spread envelope that E1 is allowed to price.

## Verdict

- E0 pass: **true**.
- E1 preregistration admitted: **true**.
- Next admitted step: E1 Spread-revival pricing preregistration using the frozen E0 spread envelope.
- Frozen axis-table SHA256: `e5e7d2724585e4a997e079dd628d1efdf8829dfb00e4e0618a553fb30c2afe18`.

## Measured

The full E0 worker probe reset and stepped the selected Chrono variants
through finite obs72/action3 using one no-op control step per variant.

| variant | model | tire | target mass kg | total mass kg | wheelbase m | wheeltrack m | result |
|---|---|---|---:|---:|---:|---|---|
| `sedan_tmeasy` | Sedan | TMEASY | 1450.0 | 1450.0 | 2.776 | `[1.5958, 1.6]` | pass |
| `bmw_e90_tmeasy` | BMW_E90 | TMEASY | 1800.0 | 1800.0 | 2.776 | `[1.500124, 1.4986]` | pass |
| `uazbus_tmeasy` | UAZBUS | TMEASY | 2858.0 | 2858.0 | 2.300 | `[1.465, 1.465]` | pass |

## Frozen Axis Table

| axis | control class | E1 status | mechanism | E1 use |
|---|---|---|---|---|
| `vehicle_model_fixture` | `discrete_reset_time_selector` | `admitted_for_e1_primary_population_axis` | scenario['chrono_vehicle_variant'] selects a whitelisted Chrono wrapper at reset | Use as the primary E1 vehicle-class spread axis crossed with frozen T-limit cells. |
| `wheelbase_and_track` | `discrete_variant_fixture` | `admitted_for_e1_variant_metadata` | Chrono backend_info reports wheelbase and wheeltrack from the selected wrapper | Use for stratification and mechanism interpretation, not as an independently swept axis. |
| `target_total_mass` | `continuous_reset_time_partial` | `admitted_with_limits` | scenario params.mass is matched by overriding Chrono chassis mass | May be used as a total-mass stress within a selected fixture if preregistered; E1 must keep it separate from payload-position or CG-height claims. |
| `payload_position_or_cg_height` | `not_exposed_by_current_backend` | `blocked_requires_connector` | no scenario key currently sets chassis CG height or payload position | Not allowed as an independent E1 axis until a backend connector exposes it and is smoked. |
| `load_transfer` | `emergent_chrono_fixture_not_direct_axis` | `admitted_as_fixture_physics_with_limits` | Chrono multibody vehicle dynamics include normal-load transfer inside each selected fixture, but E0 cannot independently sweep h_cg or axle load split. | E1 may say it prices the selected Chrono fixtures with load-transfer physics active. |
| `tire_parameter_set` | `discrete_variant_bound_fixture` | `admitted_with_limits` | all whitelisted variants use TMeasy, with tire fixtures bound to the vehicle wrapper | May be interpreted only as vehicle-bound TMeasy fixture variation; not as an independent tire-set sweep. |
| `tire_model_family` | `not_exposed_by_current_selector` | `blocked_requires_connector` | whitelisted backend selector fixes tire_model='TMEASY' for every variant | Not allowed as an E1 factor without a new selector and reset/step smoke. |
| `continuous_lf_lr_iz_cf_cr` | `not_mapped_from_scenario_params` | `blocked_requires_connector` | scenario carries lf/lr/iz/cf/cr for provenance but backend leaves fixture geometry/inertia/tires unchanged | Not allowed as independent E1 axes under the current backend. |
| `drive_brake_authority` | `control_layer_partial` | `context_only_for_e1` | drive/brake scales multiply normalized inputs and clip at 1.0 | Context/control-arm metadata only unless E1 preregisters it as a separate actuator axis. |
| `actuator_lag_and_steer_rate` | `mapped_control_layer` | `context_only_for_e1` | AutoDrift first-order/rate actuator filter is applied before Chrono driver inputs | May remain fixed from source rows; separate actuator-spread pricing requires its own preregistration. |
| `surface_mu` | `mapped_surface_axis` | `not_vehicle_spread_but_available` | scenario mu maps to Chrono FlatTerrain friction; friction step maps terrain mu replacement | Use only as the frozen T-limit surface/context axis, not as a vehicle-spread axis. |
| `split_mu_or_per_wheel_contact_surface` | `not_exposed_in_executable_env_path` | `blocked_requires_backend_connector` | current executable path exposes one FlatTerrain scalar friction coefficient | Not allowed for E1 unless a per-wheel/per-side terrain connector is added and smoked. |

## Inferred

E1 may price selected Chrono vehicle fixtures with load-transfer physics
active. It may not claim an independent payload-position, h_cg,
tire-family, split-mu, or continuous lf/lr/Iz/cf/cr sweep without a
new connector and reset/step smoke.

Recommended E1 population panel:

- Vehicle variants: `sedan_tmeasy`, `bmw_e90_tmeasy`, `uazbus_tmeasy`.
- Surface: T-limit rows only until E1 preregisters any additional surface axis.
- Arms: fixed* / RLS-retuned / per-instance tuned / per-instance Chrono-native oracle.
- Required language: E1 prices selected Chrono vehicle fixtures with load-transfer physics active; it does not price independent payload-position, h_cg, tire-family, or continuous lf/lr/Iz/cf/cr axes.

Blocked without a new connector:

- `payload_position_or_cg_height`: Not allowed as an independent E1 axis until a backend connector exposes it and is smoked.
- `tire_model_family`: Not allowed as an E1 factor without a new selector and reset/step smoke.
- `continuous_lf_lr_iz_cf_cr`: Not allowed as independent E1 axes under the current backend.
- `split_mu_or_per_wheel_contact_surface`: Not allowed for E1 unless a per-wheel/per-side terrain connector is added and smoked.

## Claim Boundary

Phase-4 E0 Chrono expressibility audit only: freezes the vehicle-spread axes currently expressible by the Chrono worker/backend and declares the spread envelope that E1 may price. It is zero training and does not make a driver-performance, high-fidelity sufficiency, validation ranking, promotion, repair-success, feasibility-proof, robustness, paper, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/chrono_spread_expressibility_prereg.json`
- Full JSON: `experiments/feasibility_audit/chrono_spread_expressibility_audit.json`
- Variant rows: `runs/feasibility_audit/chrono_spread_expressibility/variant_reset_rows.csv`
- Metrics: `runs/feasibility_audit/chrono_spread_expressibility/metrics.csv`
- Script: `scripts/feasibility_audit/chrono_spread_expressibility_audit.py`
