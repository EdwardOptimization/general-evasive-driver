import torch

from autodrift.row15_unsafe_margin_projection_probe import (
    _alpha_row15_pass,
    alpha_label,
    interpolate_state,
    parse_alphas,
)


def test_parse_alphas_keeps_order_and_deduplicates():
    assert parse_alphas("0,0.1,0.1,1") == (0.0, 0.1, 1.0)


def test_alpha_label_is_path_friendly():
    assert alpha_label(0.25) == "alpha_0_25"
    assert alpha_label(1.0) == "alpha_1"


def test_interpolate_state_interpolates_floating_tensors():
    base = {"a": torch.tensor([0.0, 2.0]), "b": torch.tensor([1], dtype=torch.int64)}
    target = {"a": torch.tensor([2.0, 6.0]), "b": torch.tensor([5], dtype=torch.int64)}

    state = interpolate_state(base, target, 0.25)

    assert torch.allclose(state["a"], torch.tensor([0.5, 3.0]))
    assert torch.equal(state["b"], torch.tensor([1], dtype=torch.int64))


def test_alpha_row15_pass_requires_all_surfaces_and_nonzero_alpha():
    rows = []
    for surface in ("a", "b", "c", "d", "e"):
        rows.append(
            {
                "surface_label": surface,
                "alpha": 0.1,
                "row15_unsafe_margin_pass": True,
            }
        )
        rows.append(
            {
                "surface_label": surface,
                "alpha": 0.0,
                "row15_unsafe_margin_pass": True,
            }
        )
    rows.append({"surface_label": "a", "alpha": 0.2, "row15_unsafe_margin_pass": True})

    result = _alpha_row15_pass(rows)

    assert result[0.1] is True
    assert result[0.0] is False
    assert result[0.2] is False
