from __future__ import annotations

import argparse

from autodrift.current_base_source_rich_adapter import (
    POLICY_LABEL,
    REQUIRED_SOURCE_RICH_METADATA_FIELDS,
    build_arg_parser,
    classify_adapter_result,
    enrich_source_group,
    missing_required_metadata_fields,
)
from autodrift.extreme_dynamics_scenario_corpus import FaultSpec, NOMINAL_FAULT


def test_parser_does_not_accept_residual_head_argument() -> None:
    parser = build_arg_parser()

    assert "--residual-head" not in parser._option_string_actions
    try:
        parser.parse_args(
            [
                "--checkpoint",
                "checkpoint.pt",
                "--scenario-config",
                "scenario.json",
                "--run-dir",
                "run",
                "--residual-head",
                "head.pt",
            ]
        )
    except SystemExit:
        pass
    else:
        raise AssertionError("parser unexpectedly accepted --residual-head")


def test_missing_required_metadata_fields_detects_adapter_contract() -> None:
    complete = {field: "value" for field in REQUIRED_SOURCE_RICH_METADATA_FIELDS}
    complete["policy_label"] = POLICY_LABEL
    complete["residual_head_required"] = False

    assert missing_required_metadata_fields([complete]) == []

    incomplete = dict(complete)
    incomplete.pop("target_obstacle_body_x")
    assert missing_required_metadata_fields([incomplete]) == ["target_obstacle_body_x"]


def test_enrich_source_group_adds_fault_fidelity_and_onset() -> None:
    fault = FaultSpec(
        name="surprise_fault",
        family="brake_authority_drop",
        severity="severe",
        activation_step=25,
        params={"max_brake_force_scale": 0.4},
        fidelity_class="current_model_fault",
    )
    group = {
        "source_group_id": 3,
        "seed": 12,
        "warmup_mode": "brake_tap",
        "preferred_fault": fault.name,
        "preferred_fault_family": fault.family,
        "preferred_fault_severity": fault.severity,
        "wrong_fault": NOMINAL_FAULT.name,
        "wrong_fault_family": NOMINAL_FAULT.family,
        "fault_family_pair": f"{fault.family}->{NOMINAL_FAULT.family}",
        "source_axis": "source_state",
        "fault_activation_step_delta": 0,
        "fault_severity_delta": 0.0,
        "fault_param_key": "",
        "modified_fault_params_json": "{}",
    }

    enriched = enrich_source_group(group, preferred_fault=fault)

    assert enriched["preferred_fault_fidelity_class"] == "current_model_fault"
    assert enriched["wrong_fault_fidelity_class"] == "current_model_fault"
    assert enriched["fault_onset_bucket"] == "mid"


def test_classify_adapter_result() -> None:
    assert (
        classify_adapter_result(
            actor_changed=False,
            warmup_artifact_rows=0,
            source_snapshots=2,
            plan_rows=3,
            missing_metadata_fields=[],
        )
        == "current_base_source_rich_adapter_metadata_ready"
    )
    assert (
        classify_adapter_result(
            actor_changed=True,
            warmup_artifact_rows=0,
            source_snapshots=2,
            plan_rows=3,
            missing_metadata_fields=[],
        )
        == "current_base_source_rich_adapter_contract_violation"
    )
    assert (
        classify_adapter_result(
            actor_changed=False,
            warmup_artifact_rows=0,
            source_snapshots=2,
            plan_rows=3,
            missing_metadata_fields=["seed"],
        )
        == "current_base_source_rich_adapter_missing_metadata"
    )


def test_parse_defaults_are_real_tuples() -> None:
    parser = build_arg_parser()
    args = parser.parse_args(
        [
            "--checkpoint",
            "checkpoint.pt",
            "--scenario-config",
            "scenario.json",
            "--run-dir",
            "run",
        ]
    )

    assert isinstance(args.obstacle_timing_deltas, tuple)
    assert isinstance(args.lateral_deltas, tuple)
    assert isinstance(args.half_width_deltas, tuple)
    assert isinstance(args.target_margins, tuple)
    assert all(isinstance(value, float) for value in args.target_margins)
