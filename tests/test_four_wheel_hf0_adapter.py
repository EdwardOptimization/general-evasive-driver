import numpy as np
import pytest

from autodrift.four_wheel_hf0_adapter import (
    FourWheelHF0Backend,
    run_source_only_four_wheel_adapter_preflight,
)
from autodrift.high_fidelity_interface import (
    ACTION_DIM,
    BackendResetRequest,
    P0_OBSERVATION_DIM,
    P0ObservationExtractor,
)


def test_four_wheel_backend_reset_and_step_emit_p0_observation():
    backend = FourWheelHF0Backend()
    extractor = P0ObservationExtractor()

    reset_result = backend.reset(BackendResetRequest(seed=2478))
    reset_observation = extractor.extract(reset_result.actor_view)

    assert reset_observation.shape == (P0_OBSERVATION_DIM,)
    assert reset_result.diagnostics["four_wheel_hidden_diagnostics_present"] is True
    assert reset_result.diagnostics["wheel_forces"] == []

    step_result = backend.step(np.array([0.25, -0.25, -0.75], dtype=np.float32))
    step_observation = extractor.extract(step_result.actor_view)

    assert step_observation.shape == (P0_OBSERVATION_DIM,)
    assert step_result.backend_status == "running"
    assert len(step_result.diagnostics["wheel_forces"]) == 4
    assert "fault_scales" in step_result.diagnostics
    assert step_result.diagnostics["physical_control"] == pytest.approx([0.25, 0.375, 0.125])


def test_four_wheel_backend_rejects_invalid_action_shape():
    backend = FourWheelHF0Backend()
    backend.reset(BackendResetRequest(seed=2478))

    with pytest.raises(ValueError, match="expected action shape"):
        backend.step(np.zeros((1, ACTION_DIM), dtype=np.float32))


def test_source_only_four_wheel_adapter_preflight_summary_flags():
    summary = run_source_only_four_wheel_adapter_preflight(actions=((0.0, 0.0, 0.0),))

    assert summary["status_pass"] is True
    assert summary["observation_shape"] == P0_OBSERVATION_DIM
    assert summary["step_observation_shapes"] == [P0_OBSERVATION_DIM]
    assert summary["action_shape"] == ACTION_DIM
    assert summary["diagnostic_wheel_force_counts"] == [4]
    assert summary["four_wheel_hidden_diagnostics_present"] is True
    assert summary["fault_scales_diagnostic_only"] is True
    assert summary["wheel_forces_diagnostic_only"] is True
    assert summary["actor_input_contract_changed"] is False
    assert summary["action_contract_changed"] is False
    assert summary["hidden_values_enter_actor_input"] is False
    assert summary["oracle_labels_enter_actor_input"] is False
    assert summary["diagnostics_available_to_actor"] is False
    assert summary["external_high_fidelity_imported"] is False
    assert summary["high_fidelity_simulation_run"] is False
