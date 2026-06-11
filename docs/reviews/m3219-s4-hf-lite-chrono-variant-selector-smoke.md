# M3219 Review: S4-HF-lite Chrono Variant-Selector Smoke

Status: accepted as an infrastructure connector.

## Findings

No blocking issues found. The default Chrono path remains selector-free
`sedan_tmeasy`, preserving the HF4 behavior surface unless a scenario
explicitly requests a different `chrono_vehicle_variant`.

The smoke is correctly scoped. It resets and steps default Sedan, BMW_E90,
and UAZBUS through the JSONL worker and obs72/action3 contract. It does not
run the incumbent driver, does not price S4, and does not claim high-fidelity
sufficiency.

The remaining limitation is explicit: sampled `lf/lr/iz/cf/cr` are still not
mapped continuously into Chrono dynamics. S4 pricing can be pre-registered
against selected vehicle wrappers, but the preregistration must decide how to
handle those lateral/tire channels.

## Decision

Accept M3219 as complete. Variant-selector reset/step smoke passed, so the
next admissible step is a frozen S4-HF-lite pricing pre-registration. A
pricing run is not admitted until that pre-registration exists.

## Checks

- `PYTHONPATH=src python scripts/feasibility_audit/s4_hf_lite_variant_selector_smoke.py`
- `PYTHONPATH=src python scripts/feasibility_audit/chrono_backend_smoke.py`
- `python -m pytest -q tests/test_chrono_vehicle_backend_variants.py`
