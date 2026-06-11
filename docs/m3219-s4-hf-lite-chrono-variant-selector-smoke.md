# M3219 S4-HF-lite Chrono Variant-Selector Smoke

Status: completed. This is a reset/step infrastructure smoke for the
S4-HF-lite route; it is not S4 pricing, not a driver-performance result, and
not RL evidence.

## Verdict

- Variant selector smoke: **pass**.
- Default behavior preserved: scenario without `chrono_vehicle_variant` resets
  as `sedan_tmeasy`.
- Explicit variants smoked: `bmw_e90_tmeasy`, `uazbus_tmeasy`.
- Next admitted step: write a frozen S4-HF-lite pricing pre-registration.
- Still not admitted: any S4 pricing run before that pre-registration exists.

## What Changed

`src/autodrift/chrono_vehicle_backend.py` now exposes a whitelisted
reset-time selector:

- `sedan_tmeasy` -> `veh.Sedan()` with TMeasy tires (default; HF4 path)
- `bmw_e90_tmeasy` -> `veh.BMW_E90()` with TMeasy tires
- `uazbus_tmeasy` -> `veh.UAZBUS()` with TMeasy tires

The selector is a scenario/backend field only. It does not enter obs72, does
not change action3, and does not touch `ActiveSafetyReflexDriver`.

## Smoke Results

`PYTHONPATH=src python scripts/feasibility_audit/s4_hf_lite_variant_selector_smoke.py`

| case | selector | Chrono model | target mass | wheelbase | wheeltracks | result |
|---|---|---|---:|---:|---|---|
| default_no_selector_sedan | omitted -> `sedan_tmeasy` | Sedan | 1450.0 kg | 2.776 m | 1.5958 / 1.6 m | pass |
| explicit_bmw_e90 | `bmw_e90_tmeasy` | BMW_E90 | 1800.0 kg | 2.776 m | 1.500124 / 1.4986 m | pass |
| explicit_uazbus | `uazbus_tmeasy` | UAZBUS | 2858.0 kg | 2.3 m | 1.465 / 1.465 m | pass |

Each case reset to finite obs72, matched the expected backend variant in
`backend_info`, matched target total mass after chassis override, and stepped
3 no-op controls without termination/truncation.

## Remaining Limits

This milestone does not map sampled `lf/lr/iz/cf/cr` continuously into Chrono
dynamics. Vehicle selection changes the base wrapper geometry/inertia/tire
fixture discretely, which is enough to admit an S4 pricing pre-registration,
but the preregistration must state how S4 handles the still-unmapped lateral
channels.

## Claim Boundary

Allowed: the existence and smoke behavior of the Chrono vehicle variant
selector, default Sedan preservation, explicit BMW_E90/UAZBUS reset/step
success, and admission of S4-HF-lite pricing pre-registration.

Rejected explicitly: driver-performance, S4/C5 pricing result, RL evidence,
high-fidelity sufficiency, validation/ranking/promotion, paper evidence, or
any mutation of the deployed v4 incumbent.

## Artifacts

- JSON: `experiments/feasibility_audit/s4_hf_lite_variant_selector_smoke.json`
- Script: `scripts/feasibility_audit/s4_hf_lite_variant_selector_smoke.py`
- Backend: `src/autodrift/chrono_vehicle_backend.py`
- Review: `docs/reviews/m3219-s4-hf-lite-chrono-variant-selector-smoke.md`
