import pandas as pd

from autodrift.family_intersection_boundary_selector import (
    boundary_rows_to_replay_corpus_frame,
    family_intersection_candidates,
    score_family_intersection_rows,
    select_compact_family_intersection_rows,
)


POLICIES = ("short61049", "short61050", "short61051")


def _boundary_row(
    index: int,
    *,
    checkpoint_label: str = "short61049",
    target: str = "future_braking_deceleration",
    pair: int | None = None,
    accepted: bool = True,
    margin_gap: float = 0.02,
) -> dict[str, object]:
    pair_id = index if pair is None else pair
    left_seed = 100 + pair_id
    right_seed = 200 + pair_id
    left_step = 10 + pair_id
    right_step = 30 + pair_id
    normal_margin = 0.01 + 0.0001 * index
    variant_margin = normal_margin - margin_gap
    return {
        "candidate_id": index,
        "source_pair_id": pair_id,
        "checkpoint_label": checkpoint_label,
        "probe_seed": 105400,
        "target": target,
        "variant": "wrong_matched_history",
        "left_seed": left_seed,
        "right_seed": right_seed,
        "left_step": left_step,
        "right_step": right_step,
        "relocated_obstacle_body_x": 8.0 + 0.01 * index,
        "relocated_obstacle_body_y": -1.0,
        "relocated_obstacle_half_width": 0.8,
        "normal_margin": normal_margin,
        "variant_margin": variant_margin,
        "normal_success": True,
        "variant_success": False,
        "success_drop": True,
        "margin_gap": margin_gap,
        "normal_first_steer": 0.1,
        "normal_first_throttle": -0.2,
        "normal_first_brake": 0.3,
        "normal_near_boundary": True,
        "accepted": accepted,
        "physical_pair_key": f"{left_seed}:{left_step}:{right_seed}:{right_step}",
    }


def _replay_row(
    *,
    policy: str,
    row_id: int,
    target: str = "future_braking_deceleration",
    normal_success: bool = True,
    wrong_success: bool = False,
    wrong_margin: float = -0.002,
    margin_gap: float = 0.02,
) -> dict[str, object]:
    return {
        "policy": policy,
        "checkpoint": f"{policy}.pt",
        "row_id": row_id,
        "target": target,
        "physical_pair_key": f"pair{row_id}",
        "left_seed": 1,
        "right_seed": 2,
        "left_step": 10,
        "right_step": 20,
        "relocated_obstacle_body_x": 8.0,
        "relocated_obstacle_body_y": -1.0,
        "relocated_obstacle_half_width": 0.8,
        "normal_success": normal_success,
        "wrong_history_success": wrong_success,
        "success_drop": bool(normal_success and not wrong_success),
        "normal_margin": 0.01,
        "wrong_history_margin": wrong_margin,
        "margin_gap": margin_gap,
    }


def test_boundary_rows_to_replay_corpus_frame_preserves_source_row_id():
    frame = pd.DataFrame(
        [
            _boundary_row(0),
            _boundary_row(1, accepted=False),
            _boundary_row(2, target="future_yaw_response"),
        ]
    )

    replay = boundary_rows_to_replay_corpus_frame(frame)

    assert replay["row_id"].tolist() == [0, 2]
    assert replay.loc[0, "physical_pair_key"] == "100:10:200:30"
    assert replay.loc[1, "target"] == "future_yaw_response"


def test_family_intersection_candidates_reject_rows_that_fail_any_policy():
    boundary = pd.DataFrame([_boundary_row(0), _boundary_row(1)])
    replay_rows = []
    for policy in POLICIES:
        replay_rows.append(_replay_row(policy=policy, row_id=0, wrong_margin=-0.003))
        replay_rows.append(
            _replay_row(
                policy=policy,
                row_id=1,
                wrong_success=(policy == "short61050"),
                wrong_margin=0.0002 if policy == "short61050" else -0.003,
            )
        )

    scored = score_family_intersection_rows(
        boundary_frame=boundary,
        replay_rows=pd.DataFrame(replay_rows),
        family_policies=POLICIES,
    )
    candidates = family_intersection_candidates(scored, min_family_success_drop_count=3)

    assert candidates["source_row_index"].tolist() == [0]
    failed = scored[scored["source_row_index"] == 1].iloc[0]
    assert "short61050:wrong_history_succeeded" in failed["family_policy_failures"]
    assert not bool(failed["family_all_wrong_history_fail"])


def test_compact_selection_uses_strict_margin_when_sufficient_and_caps_pairs():
    rows = []
    for source in POLICIES:
        for index in range(6):
            target = "future_yaw_response" if index % 2 else "future_braking_deceleration"
            row = _boundary_row(index, checkpoint_label=source, target=target, pair=index // 3)
            row.update(
                {
                    "source_row_index": index,
                    "boundary_geometry_key": f"{source}-{index}",
                    "family_policy_count": 3,
                    "family_success_drop_count": 3,
                    "family_all_normal_success": True,
                    "family_all_wrong_history_fail": True,
                    "family_all_success_drop": True,
                    "family_min_wrong_history_margin": -0.01 - 0.001 * index,
                    "family_max_wrong_history_margin": -0.001,
                    "family_min_margin_gap": 0.02 + 0.001 * index,
                    "family_policy_failures": "",
                }
            )
            rows.append(row)

    selected, summary = select_compact_family_intersection_rows(
        pd.DataFrame(rows),
        source_labels=POLICIES,
        max_rows_per_physical_pair=2,
        min_rows_per_source=4,
        min_physical_pairs_per_source=2,
        min_targets_per_source=2,
        strict_wrong_history_margin_max=-0.0001,
    )

    assert summary["all_sources_pass"]
    assert set(selected["family_selection_mode"]) == {"strict_family_margin"}
    for _, group in selected.groupby(["checkpoint_label", "physical_pair_key"], observed=True):
        assert len(group) <= 2
    for source in POLICIES:
        source_rows = selected[selected["checkpoint_label"] == source]
        assert len(source_rows) >= 4
        assert source_rows["target"].nunique() >= 2


def test_compact_selection_falls_back_when_strict_margin_is_sparse():
    rows = []
    for index in range(4):
        row = _boundary_row(index, checkpoint_label="short61049", pair=index)
        row.update(
            {
                "source_row_index": index,
                "boundary_geometry_key": f"g{index}",
                "family_policy_count": 3,
                "family_success_drop_count": 3,
                "family_all_normal_success": True,
                "family_all_wrong_history_fail": True,
                "family_all_success_drop": True,
                "family_min_wrong_history_margin": -0.002,
                "family_max_wrong_history_margin": -0.00005,
                "family_min_margin_gap": 0.02,
                "family_policy_failures": "",
            }
        )
        rows.append(row)

    selected, summary = select_compact_family_intersection_rows(
        pd.DataFrame(rows),
        source_labels=("short61049",),
        max_rows_per_physical_pair=1,
        min_rows_per_source=4,
        min_physical_pairs_per_source=4,
        min_targets_per_source=1,
        strict_wrong_history_margin_max=-0.0001,
    )

    assert summary["all_sources_pass"]
    assert set(selected["family_selection_mode"]) == {"family_intersection"}


def test_compact_selection_skips_duplicate_boundary_geometry_before_pair_cap():
    rows = []
    for index in range(5):
        row = _boundary_row(index, checkpoint_label="short61049", pair=0 if index < 3 else index)
        row.update(
            {
                "source_row_index": index,
                "boundary_geometry_key": "duplicate" if index < 3 else f"g{index}",
                "family_policy_count": 3,
                "family_success_drop_count": 3,
                "family_all_normal_success": True,
                "family_all_wrong_history_fail": True,
                "family_all_success_drop": True,
                "family_min_wrong_history_margin": -0.01 - 0.001 * index,
                "family_max_wrong_history_margin": -0.001,
                "family_min_margin_gap": 0.02 + 0.001 * index,
                "family_policy_failures": "",
            }
        )
        rows.append(row)

    selected, _ = select_compact_family_intersection_rows(
        pd.DataFrame(rows),
        source_labels=("short61049",),
        max_rows_per_physical_pair=2,
        min_rows_per_source=3,
        min_physical_pairs_per_source=2,
        min_targets_per_source=1,
        strict_wrong_history_margin_max=-0.0001,
    )

    assert selected["boundary_geometry_key"].tolist().count("duplicate") == 1
