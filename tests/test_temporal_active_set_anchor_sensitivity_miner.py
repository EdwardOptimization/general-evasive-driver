from autodrift.temporal_active_set_anchor_sensitivity_miner import (
    ANCHOR_WINDOWS,
    OVERRIDES,
    PREDECISION_WINDOWS,
    active_anchor_rows,
    anchor_step_for_window,
    apply_local_override,
    build_anchor_candidates,
    build_summary,
)


class _EnvConfig:
    max_steps = 80


class _Hook:
    def __init__(self, reveal_step: int = 20, decision_step: int = 42):
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
        self.reveal_step = 20
        self.decision_step = 42
        self.base_distance_min = 10.0
        self.base_distance_max = 20.0
        self.retarget_distance_min = 8.0
        self.retarget_distance_max = 16.0


class _Spec:
    def __init__(self, calibration_id: str, family: str, *, seed: int = 1):
        self.artifact_row = _Artifact(calibration_id, family, seed=seed)
        self.hook_spec = _Hook()


def test_anchor_step_for_window_uses_expected_temporal_offsets():
    spec = _Spec("c0", "family_a")

    assert anchor_step_for_window(spec, "reveal") == 20
    assert anchor_step_for_window(spec, "reveal_plus_4") == 24
    assert anchor_step_for_window(spec, "decision_minus_16") == 26
    assert anchor_step_for_window(spec, "decision_minus_8") == 34
    assert anchor_step_for_window(spec, "decision") == 42
    assert anchor_step_for_window(spec, "post_decision_8") == 50


def test_apply_local_override_clips_in_actor_action_space():
    action = [0.9, 0.0, 0.8]

    left_brake = apply_local_override(action, "steer_left_brake_more")
    right = apply_local_override(action, "steer_right")
    less_brake = apply_local_override(action, "brake_less")

    assert left_brake.tolist() == [1.0, 0.0, 1.0]
    assert right[0] < action[0]
    assert less_brake[2] < action[2]


def test_build_anchor_candidates_round_robins_source_families():
    specs = [_Spec(f"c{i}", f"family_{i % 4}", seed=i) for i in range(12)]

    anchors = build_anchor_candidates(specs, max_anchors=16)

    assert len(anchors) == 16
    assert len({row.source_family for row in anchors}) == 4
    assert {row.anchor_window for row in anchors} <= set(ANCHOR_WINDOWS)
    assert max(sum(1 for row in anchors if row.source_family == family) for family in {row.source_family for row in anchors}) <= 4


def _anchor_row(index: int) -> dict:
    window = ANCHOR_WINDOWS[index % len(ANCHOR_WINDOWS)]
    return {
        "anchor_id": f"anchor-{index}",
        "source_family": f"family_{index % 4}",
        "anchor_window": window,
        "normal_terminal_margin": 0.04,
        "normal_replay_status": "ok",
    }


def test_active_anchor_rows_and_summary_gate_synthetic_active_set():
    anchor_rows = [_anchor_row(index) for index in range(64)]
    local_rows = []
    for index, anchor in enumerate(anchor_rows):
        for override in OVERRIDES:
            active = index < 24 and override == OVERRIDES[0]
            success_flip = index < 3 and override == OVERRIDES[0]
            local_rows.append(
                {
                    **anchor,
                    "override": override,
                    "replay_status": "ok",
                    "abs_terminal_margin_gap_from_normal": 0.03 if active else 0.0,
                    "success_flip": success_flip,
                    "collision_flip": False,
                }
            )

    active_rows = active_anchor_rows(anchor_rows, local_rows)
    summary = build_summary(
        specs=[object()] * 64,
        anchor_rows=anchor_rows,
        local_rows=local_rows,
        active_rows=active_rows,
        max_anchors=64,
        continuation_steps=64,
    )

    assert len(active_rows) == 24
    assert summary["local_perturbation_row_count"] == 64 * len(OVERRIDES)
    assert summary["action_sensitive_anchor_count"] == 24
    assert summary["predecision_sensitive_anchor_count"] >= 6
    assert summary["success_flip_count"] == 3
    assert summary["passes_public_smoke_gates"] is True
    assert summary["passes_evidence_quality_targets"] is True
    assert all(row["anchor_window"] in PREDECISION_WINDOWS or row["predecision_anchor"] is False for row in active_rows)
