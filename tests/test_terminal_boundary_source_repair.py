from autodrift.fresh_ambiguity_history_interventions import anchor_step_for
from autodrift.fresh_ambiguity_source_mining import FreshAmbiguitySourceRow
from autodrift.terminal_boundary_source_repair import (
    REPAIR_ANCHORS,
    TERMINAL_TARGET_FAMILIES,
    build_terminal_summary,
    is_terminal_target_family,
    select_terminal_pairs,
    terminal_repair_source_rows,
)


def test_terminal_repair_source_rows_focus_on_target_and_support_families():
    rows = terminal_repair_source_rows(seed=1731, seed_count=3, max_repair_source_specs=72)

    assert len(rows) >= 35
    assert sum(1 for row in rows if row.source_family in TERMINAL_TARGET_FAMILIES) >= 20
    assert {row.source_family for row in rows} >= set(TERMINAL_TARGET_FAMILIES)
    assert all(row.candidate_materialized is False for row in rows)
    assert all(row.training_corpus_exported is False for row in rows)
    assert all(row.actor_input_contract_changed is False for row in rows)


def test_terminal_target_family_predicate_is_strict():
    assert is_terminal_target_family("t5_boundary_axis_retarget")
    assert is_terminal_target_family("late_reveal_boundary")
    assert not is_terminal_target_family("brake_fade_or_loss_proxy")
    assert not is_terminal_target_family("capability_step_down")


def test_anchor_step_supports_decision_minus_16():
    row = terminal_repair_source_rows(seed=1731, seed_count=1, max_repair_source_specs=1)[0]

    assert "decision_minus_16" in REPAIR_ANCHORS
    assert anchor_step_for(row, "decision_minus_16") == max(row.reveal_step, row.decision_step - 16)


class _Pair:
    def __init__(self, pair_id: str, left_family: str, right_family: str, accepted: bool = True):
        self.pair_id = pair_id
        self.left_trace_id = f"{left_family}|1|fresh-{left_family}-000"
        self.right_trace_id = f"{right_family}|2|fresh-{right_family}-000"
        self.left_source_family = left_family
        self.right_source_family = right_family
        self.task_family = "T5"
        self.scene_context_distance = 0.01
        self.current_ego_distance = 0.01
        self.first_action_l2 = 0.2
        self.terminal_margin_gap = 0.03
        self.accepted = accepted


def test_select_terminal_pairs_requires_accepted_terminal_side():
    pairs = [
        _Pair("a", "capability_step_down", "capability_step_up"),
        _Pair("b", "t5_near_boundary_warmup", "capability_step_up"),
        _Pair("c", "late_reveal_boundary", "curved_boundary_obstacle", accepted=False),
    ]

    selected = select_terminal_pairs(pairs, max_intervention_pairs=4)

    assert len(selected) == 1
    assert selected[0].pair_id == "b"
    assert selected[0].left_source_family == "t5_near_boundary_warmup"


def _source_row(source_family: str) -> FreshAmbiguitySourceRow:
    return FreshAmbiguitySourceRow(
        source_family=source_family,
        task_family="T5",
        source_index=0,
        seed=1,
        hidden_capability_pair="low|high",
        geometry_key="g",
        reveal_step=10,
        decision_step=18,
        simulator_scope="existing_public_source",
        proxy_fault_family=False,
        closed_t5_subset=False,
        scene_context_distance=0.01,
        current_ego_distance=0.01,
        recent_window_distance=0.01,
        older_evidence_distance=0.2,
        hidden_capability_distance=0.2,
        first_action_l2=0.2,
        prefix_action_l2=0.2,
        terminal_margin_gap=0.03,
        normal_margin=0.03,
    )


class _Attempt:
    source_family = "t5_near_boundary_warmup"
    reached_decision = True


class _Snapshot:
    snapshot_kind = "decision"
    source_family = "t5_near_boundary_warmup"
    min_clearance_margin = 0.01


def test_build_terminal_summary_reports_terminal_history_gates():
    source_rows = [_source_row("t5_near_boundary_warmup") for _ in range(30)]
    pair = _Pair("p", "t5_near_boundary_warmup", "t5_boundary_axis_retarget")
    accepted = select_terminal_pairs([pair])
    rows = [
        {
            "pair_id": "p",
            "target_side": "left",
            "anchor_name": "decision",
            "variant": "wrong_history_donor_hidden_at_anchor",
            "target_source_family": "t5_near_boundary_warmup",
            "terminal_margin_gap_from_normal": 0.03,
            "success_drop_from_normal": False,
            "target_replay_status": "ok",
        },
        {
            "pair_id": "p",
            "target_side": "left",
            "anchor_name": "decision_minus_8",
            "variant": "donor_response_action_plus_hidden_from_anchor",
            "target_source_family": "t5_near_boundary_warmup",
            "terminal_margin_gap_from_normal": 0.04,
            "success_drop_from_normal": True,
            "target_replay_status": "ok",
        },
    ]

    summary = build_terminal_summary(
        source_rows=source_rows,
        attempts=[_Attempt() for _ in range(20)],
        snapshots=[_Snapshot() for _ in range(8)],
        pairs=accepted,
        rows=rows,
        max_intervention_pairs=24,
        continuation_steps=64,
    )

    assert summary["terminal_source_spec_count"] == 30
    assert summary["terminal_wrong_history_positive_target_sides"] == 1
    assert summary["terminal_donor_plus_hidden_positive_target_sides"] == 1
    assert summary["terminal_wrong_or_donor_success_drop_count"] == 1
    assert summary["passes_terminal_history_gates"] is True
    assert summary["candidate_materialized"] is False
