from __future__ import annotations

from autodrift.high_speed_late_history_source_repair import (
    FALLBACK_HIDDEN_L2_MIN,
    FALLBACK_RESPONSE_ACTION_L2_MAX,
    STRICT_HIDDEN_L2_MIN,
    STRICT_RESPONSE_ACTION_L2_MAX,
    donor_screen_label,
    high_speed_history_pressure_modes,
    late_history_pressure_modes,
    repair_anchor_step_for_window,
)


class _Hook:
    reveal_step = 20
    decision_step = 52

    class env_config:
        max_steps = 80


class _Spec:
    hook_spec = _Hook()


def test_history_pressure_modes_cover_low_authority_and_aeb() -> None:
    high_speed = high_speed_history_pressure_modes()
    late = late_history_pressure_modes()

    assert any(mode.low_authority_band for mode in high_speed)
    assert any(mode.require_aeb_infeasible for mode in high_speed)
    assert any(mode.low_authority_band for mode in late)
    assert any(mode.require_aeb_infeasible for mode in late)
    assert any(mode.reveal_delta < 0 for mode in high_speed)
    assert any(mode.reveal_delta >= 10 for mode in late)


def test_donor_screen_label() -> None:
    assert (
        donor_screen_label(
            response_action_l2=STRICT_RESPONSE_ACTION_L2_MAX,
            hidden_l2=STRICT_HIDDEN_L2_MIN,
        )
        == "strict_matched_current_hidden_divergent"
    )
    assert (
        donor_screen_label(
            response_action_l2=FALLBACK_RESPONSE_ACTION_L2_MAX,
            hidden_l2=FALLBACK_HIDDEN_L2_MIN,
        )
        == "fallback_matched_current_hidden_divergent"
    )
    assert donor_screen_label(response_action_l2=0.9, hidden_l2=10.0) == "screen_rejected"
    assert donor_screen_label(response_action_l2=0.2, hidden_l2=1.0) == "screen_rejected"


def test_repair_anchor_step_for_window() -> None:
    assert repair_anchor_step_for_window(_Spec(), "reveal_plus_2") == 22
    assert repair_anchor_step_for_window(_Spec(), "reveal_plus_8") == 28
    assert repair_anchor_step_for_window(_Spec(), "decision_minus_32") == 20
    assert repair_anchor_step_for_window(_Spec(), "decision") == 52
