from __future__ import annotations

from pathlib import Path

from autodrift.artifacts import write_csv_rows
from autodrift.v4_pair_delta_objective_target_enrichment import (
    build_sequence_index,
    classify_target_enrichment,
    enrich_rows,
    join_key,
    run_target_enrichment,
    sequence_source_name,
)


def _row(**overrides):
    row = {
        "pair_id": "1",
        "left_candidate_id": "10",
        "right_candidate_id": "20",
        "left_source_group_id": "30",
        "right_source_group_id": "40",
        "left_seed": "78058",
        "right_seed": "78055",
        "left_fault_family": "combined_fault",
        "right_fault_family": "combined_fault",
        "left_step": "8",
        "right_step": "8",
        "direction": "pair_delta_positive",
        "direction_family": "pair_delta",
        "hold_steps": "6",
        "epsilon_l2": "0.075",
        "normal_margin": "0.010",
        "sequence_margin": "0.025",
        "effective_delta_l2_mean": "0.075",
        "effective_sequence_l2": "0.18",
        "clip_fraction_max": "0.0",
        "severe_clip_steps": "0",
        "dedup_signature": "sig-1",
        "duplicate_row_count": "1",
        "duplicate_retarget_axes": "",
        "duplicate_pair_ids": "1",
        "evidence_origin": "existing_m867_or_m870",
        "dedup_role": "canonical",
        "objective_sample_weight": "1.0",
    }
    row.update(overrides)
    return row


def _sequence(**overrides):
    row = _row(**overrides)
    row.update(
        {
            "normal_first_steer": "0.1",
            "normal_first_throttle": "0.2",
            "normal_first_brake": "0.0",
            "right_first_steer": "-0.1",
            "right_first_throttle": "0.1",
            "right_first_brake": "0.0",
            "first_override_steer": "0.15",
            "first_override_throttle": "0.2",
            "first_override_brake": "0.0",
            "requested_delta_l2_per_step": "0.075",
            "effective_delta_l2_max": "0.075",
            "clip_fraction_mean": "0.0",
            "first_action_l2_vs_normal": "0.075",
            "prefix_l2_mean_vs_normal": "0.05",
            "prefix_l2_max_vs_normal": "0.075",
            "terminal_reason": "obstacle_completed",
            "steps": "44",
        }
    )
    return row


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    write_csv_rows(path, rows)


def test_join_key_uses_identity_fields() -> None:
    row = _row(pair_id="99", direction="pair_delta_negative")

    key = join_key(row)

    assert "99" in key
    assert "pair_delta_negative" in key
    assert "sig-1" not in key


def test_sequence_source_name_labels_known_sources() -> None:
    assert sequence_source_name(Path("runs/m867_x/pair_delta_sequence_rows.csv")) == "m867_sequence"
    assert sequence_source_name(Path("runs/m873_x/pair_delta_sequence_rows.csv")) == "m873_boundary_preserving_sequence"


def test_enrich_rows_restores_action_targets_from_sequence_index(tmp_path: Path) -> None:
    sequence_path = tmp_path / "m867_pair_delta_sequence_rows.csv"
    _write(sequence_path, [_sequence()])
    by_identity, by_signature = build_sequence_index([sequence_path])

    enriched, joins = enrich_rows([_row()], by_identity, by_signature)

    assert enriched[0]["normal_first_steer"] == "0.1"
    assert enriched[0]["first_override_steer"] == "0.15"
    assert enriched[0]["sequence_source"] == "m867_sequence"
    assert joins[0]["enrichment_join_status"] == "identity_unique"
    assert joins[0]["target_action_fields_present"] is True


def test_enrich_rows_reports_missing_join() -> None:
    enriched, joins = enrich_rows([_row()], {}, {})

    assert enriched[0]["enrichment_join_status"] == "missing"
    assert joins[0]["target_action_fields_present"] is False


def test_classify_target_enrichment_pass() -> None:
    result = classify_target_enrichment(
        dedup_rows_enriched=10,
        missing_join_count=0,
        ambiguous_join_count=0,
        target_action_fields_present=True,
        split_labels_preserved=True,
        duplicate_metadata_preserved=True,
        caveat_78055_recorded=True,
    )

    assert result == "v4_pair_delta_objective_target_enrichment_pass"


def test_run_target_enrichment_writes_artifacts(tmp_path: Path) -> None:
    dedup = [_row()]
    train = [{**_row(), "split": "objective_train_public"}]
    eval_rows = [{**_row(pair_id="2", sequence_margin="0.030", dedup_signature="sig-2"), "split": "objective_eval_public"}]
    holdout = [{**_row(pair_id="3", sequence_margin="0.035", dedup_signature="sig-3"), "split": "source_holdout_public"}]
    signature = [{**_row(pair_id="4", sequence_margin="0.040", dedup_signature="sig-4"), "split": "new_signature_holdout_public"}]
    sequences = [
        _sequence(),
        _sequence(pair_id="2", sequence_margin="0.030", dedup_signature="sig-2"),
        _sequence(pair_id="3", sequence_margin="0.035", dedup_signature="sig-3"),
        _sequence(pair_id="4", sequence_margin="0.040", dedup_signature="sig-4"),
    ]
    _write(tmp_path / "dedup.csv", dedup)
    _write(tmp_path / "train.csv", train)
    _write(tmp_path / "eval.csv", eval_rows)
    _write(tmp_path / "holdout.csv", holdout)
    _write(tmp_path / "signature.csv", signature)
    _write(tmp_path / "m867_sequence.csv", sequences)

    summary = run_target_enrichment(
        dedup_rows_path=tmp_path / "dedup.csv",
        objective_train_rows_path=tmp_path / "train.csv",
        objective_eval_rows_path=tmp_path / "eval.csv",
        source_holdout_rows_path=tmp_path / "holdout.csv",
        new_signature_holdout_rows_path=tmp_path / "signature.csv",
        sequence_rows_paths=[tmp_path / "m867_sequence.csv"],
        run_dir=tmp_path / "run",
    )

    assert summary["result_class"] == "v4_pair_delta_objective_target_enrichment_pass"
    assert summary["missing_join_count"] == 0
    assert (tmp_path / "run" / "enriched_dedup_pair_delta_rows.csv").exists()
