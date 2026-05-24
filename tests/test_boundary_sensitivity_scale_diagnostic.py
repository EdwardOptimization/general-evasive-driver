from autodrift.boundary_sensitivity_scale_diagnostic import (
    classify_scale_diagnostic,
    deltas_for_scale,
    parse_scale,
    slug_float,
)


def test_parse_scale_assigns_classes():
    local = parse_scale("local=0.04,0.06,0.06")
    stress = parse_scale("stress=0.12,0.20,0.20")
    probe = parse_scale("unrealistic_probe=0.20,0.35,0.35")

    assert local.scale_class == "plausible"
    assert stress.scale_class == "stress"
    assert probe.scale_class == "unrealistic"


def test_deltas_for_scale_include_half_and_full():
    assert deltas_for_scale(0.04) == (-0.04, -0.02, 0.02, 0.04)


def test_slug_float_handles_negative_values():
    assert slug_float(2.0) == "2"
    assert slug_float(-1.0) == "m1"
    assert slug_float(0.5) == "0p5"


def test_classify_scale_diagnostic_prefers_plausible_positive():
    rows = [
        {"scale_class": "stress", "scale_name": "stress", "accepted_rows": 10, "result_class": "fresh_source_sparse"},
        {
            "scale_class": "plausible",
            "scale_name": "plausible",
            "accepted_rows": 90,
            "result_class": "fresh_source_positive",
        },
    ]

    assert classify_scale_diagnostic(rows) == "scale_positive_plausible"


def test_classify_scale_diagnostic_separates_stress_only():
    rows = [
        {"scale_class": "plausible", "scale_name": "local", "accepted_rows": 0, "result_class": "fresh_surface_empty"},
        {
            "scale_class": "stress",
            "scale_name": "stress",
            "accepted_rows": 80,
            "result_class": "fresh_source_positive",
        },
    ]

    assert classify_scale_diagnostic(rows) == "scale_positive_stress_only"


def test_classify_scale_diagnostic_does_not_promote_sparse_plausible_rows():
    rows = [
        {
            "scale_class": "plausible",
            "scale_name": "plausible",
            "accepted_rows": 2,
            "result_class": "history_insensitive",
        },
        {"scale_class": "stress", "scale_name": "stress", "accepted_rows": 0, "result_class": "fresh_surface_empty"},
    ]

    assert classify_scale_diagnostic(rows) == "scale_sparse_plausible"


def test_classify_scale_diagnostic_empty():
    rows = [
        {"scale_class": "plausible", "scale_name": "local", "accepted_rows": 0, "result_class": "fresh_surface_empty"},
        {"scale_class": "stress", "scale_name": "stress", "accepted_rows": 0, "result_class": "fresh_surface_empty"},
    ]

    assert classify_scale_diagnostic(rows) == "scale_empty"
