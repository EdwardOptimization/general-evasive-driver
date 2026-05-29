from autodrift.recoverable_active_set_generator import (
    ANCHOR_WINDOWS,
    HOLD_STEPS,
    LOCAL_OVERRIDES,
    apply_local_override,
    build_anchor_candidates,
    build_summary,
    classify_anchor,
    recoverable_active_anchor_rows,
)


class _EnvConfig:
    max_steps = 90


class _Hook:
    def __init__(self, reveal_step: int = 22, decision_step: int = 50):
        self.reveal_step = reveal_step
        self.decision_step = decision_step
        self.env_config = _EnvConfig()


class _Artifact:
    def __init__(self, calibration_id: str, family: str, *, seed: int = 1):
        self.calibration_id = calibration_id
        self.source_row_id = f"source-{calibration_id}"
        self.source_family = family
        self.task_family = "T5"
        self.seed = seed
        self.mode_name = "mode"
        self.reveal_step = 22
        self.decision_step = 50
        self.base_distance_min = 10.0
        self.base_distance_max = 20.0
        self.retarget_distance_min = 8.0
        self.retarget_distance_max = 16.0


class _Spec:
    def __init__(self, calibration_id: str, family: str, *, seed: int = 1):
        self.artifact_row = _Artifact(calibration_id, family, seed=seed)
        self.hook_spec = _Hook()


def test_apply_local_override_handles_release_and_compounds():
    action = [0.9, 0.4, -0.8]

    release = apply_local_override(action, "throttle_release")
    left_less = apply_local_override(action, "steer_left_brake_less")
    right_more = apply_local_override(action, "steer_right_brake_more")

    assert abs(float(release[0]) - action[0]) < 1e-6
    assert release[1] == -1.0
    assert abs(float(release[2]) - action[2]) < 1e-6
    assert left_less[0] == 1.0
    assert left_less[2] < action[2]
    assert right_more[0] < action[0]
    assert right_more[2] > action[2]


def test_build_anchor_candidates_uses_recoverable_windows_and_round_robin():
    specs = [_Spec(f"c{i}", f"family_{i % 5}", seed=i) for i in range(20)]

    anchors = build_anchor_candidates(specs, max_anchors=25)

    assert len(anchors) == 25
    assert len({row.source_family for row in anchors}) == 5
    assert {row.anchor_window for row in anchors} <= set(ANCHOR_WINDOWS)


def test_classify_anchor_separates_recoverable_and_unrecoverable():
    anchor = {
        "anchor_id": "a0",
        "normal_replay_status": "ok",
        "normal_terminal_margin": 0.04,
        "normal_success": False,
        "normal_collision": True,
    }
    rows = [
        {
            "replay_status": "ok",
            "abs_terminal_margin_gap_from_normal": 0.06,
            "success_flip": False,
            "collision_flip": True,
            "override": "steer_left",
            "hold_steps": 8,
        }
    ]

    result = classify_anchor(anchor, rows)

    assert result["triage_label"] == "strong_recoverable_boundary"
    assert result["recoverable_boundary"] is True
    assert result["strong_recoverable_boundary"] is True
    assert result["best_override"] == "steer_left"
    assert result["best_hold_steps"] == 8


def test_recoverable_active_anchor_rows_and_summary_gates_synthetic():
    anchor_rows = []
    local_rows = []
    for index in range(256):
        label_source = f"family_{index % 5}"
        window = ANCHOR_WINDOWS[index % len(ANCHOR_WINDOWS)]
        anchor = {
            "anchor_id": f"anchor-{index}",
            "source_family": label_source,
            "anchor_window": window,
            "normal_replay_status": "ok",
            "normal_terminal_margin": 0.10 if index < 60 else 1.0,
            "normal_success": index >= 60,
            "normal_collision": index < 60,
            "normal_terminal_reason": "collision" if index < 60 else "obstacle_completed",
        }
        anchor_rows.append(anchor)
        for override in LOCAL_OVERRIDES:
            for hold_steps in HOLD_STEPS:
                active = index < 60 and override == LOCAL_OVERRIDES[0] and hold_steps == 8
                local_rows.append(
                    {
                        **anchor,
                        "override": override,
                        "hold_steps": hold_steps,
                        "replay_status": "ok",
                        "abs_terminal_margin_gap_from_normal": 0.06 if active else 0.0,
                        "success_flip": active and index < 12,
                        "collision_flip": active and index < 16,
                    }
                )

    triage_rows = recoverable_active_anchor_rows(anchor_rows, local_rows)
    summary = build_summary(
        specs=[object()] * 240,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        triage_rows=triage_rows,
        max_source_specs=240,
        max_anchors=256,
        continuation_steps=64,
    )

    assert summary["local_hold_row_count"] == 256 * len(LOCAL_OVERRIDES) * len(HOLD_STEPS)
    assert summary["recoverable_boundary_anchor_count"] == 60
    assert summary["strong_recoverable_boundary_anchor_count"] == 60
    assert summary["predecision_recoverable_anchor_count"] >= 12
    assert summary["active_source_family_count"] == 5
    assert summary["collision_flip_count"] == 16
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True
