from autodrift.chrono_vehicle_backend import (
    CHRONO_VEHICLE_VARIANTS,
    DEFAULT_CHRONO_VEHICLE_VARIANT,
    smoke_scenario,
)


def test_chrono_vehicle_variant_catalog_has_default_and_s4_smoke_variants():
    assert DEFAULT_CHRONO_VEHICLE_VARIANT == "sedan_tmeasy"
    assert DEFAULT_CHRONO_VEHICLE_VARIANT in CHRONO_VEHICLE_VARIANTS
    assert CHRONO_VEHICLE_VARIANTS[DEFAULT_CHRONO_VEHICLE_VARIANT].constructor_name == "Sedan"
    assert CHRONO_VEHICLE_VARIANTS["bmw_e90_tmeasy"].constructor_name == "BMW_E90"
    assert CHRONO_VEHICLE_VARIANTS["uazbus_tmeasy"].constructor_name == "UAZBUS"


def test_chrono_smoke_scenario_keeps_selector_out_unless_requested():
    scenario = smoke_scenario(93210, 0.8, max_steps=12)

    assert "chrono_vehicle_variant" not in scenario
    assert scenario["params"]["mass"] == 1450.0
    assert scenario["dt"] == 0.02
