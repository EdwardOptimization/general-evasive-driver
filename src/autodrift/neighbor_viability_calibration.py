"""Neighbor-source viability calibration candidate generator."""

from __future__ import annotations

import argparse
import math
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.source_step_replay_boundary_retarget import DEFAULT_MIN_HALF_WIDTH
from autodrift.warmup_latched_outcome_probe import CONTROL_VARIANTS, WARMUP_HISTORY_VARIANTS, source_diversity


DEFAULT_NEAR_MARGIN_HIGH = 1.0
DEFAULT_MIN_SEQUENCE_ACTION_L2 = 0.025


def _finite(value: Any, default: float = float("nan")) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float(default)
    return result if math.isfinite(result) else float(default)


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(float(value) != 0.0) if math.isfinite(float(value)) else False
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _source_step(row: dict[str, Any]) -> int:
    return int(_finite(row.get("source_step"), _finite(row.get("candidate_step"), _finite(row.get("reveal_step"), 0.0))))


def source_family_signature(row: dict[str, Any]) -> str:
    return "|".join(
        str(row.get(field, ""))
        for field in (
            "seed",
            "candidate_step",
            "preferred_fault",
            "wrong_fault",
            "capability_pair",
            "preferred_reveal_bucket",
        )
    )


def original_source_families(history_positive_rows: pd.DataFrame) -> set[str]:
    if history_positive_rows.empty:
        return set()
    frame = history_positive_rows.copy()
    if "history_positive" in frame:
        frame = frame[frame["history_positive"].map(_bool_value)]
    if "control_positive" in frame:
        frame = frame[~frame["control_positive"].map(_bool_value)]
    return {source_family_signature(row) for row in frame.to_dict("records")}


def classify_viability(
    *,
    normal_success: bool,
    normal_margin: float,
    margin_gap: float,
    near_margin_high: float = DEFAULT_NEAR_MARGIN_HIGH,
) -> str:
    if not normal_success or not math.isfinite(normal_margin) or normal_margin < 0.0:
        return "too_hard"
    if normal_margin <= float(near_margin_high) and margin_gap >= 0.0:
        return "near_boundary"
    return "too_easy"


def _away_direction(y: float) -> float:
    if not math.isfinite(y) or abs(y) < 1e-9:
        return 0.0
    return 1.0 if y > 0.0 else -1.0


def _center_direction(y: float) -> float:
    return -_away_direction(y)


def calibration_delta_grid(viability_class: str, *, relocated_body_y: float) -> list[dict[str, float]]:
    if viability_class == "too_hard":
        away = _away_direction(relocated_body_y)
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": away * dy, "half_width_delta": dw}
            for dx in (1.0, 2.0, 3.0)
            for dy in (0.0, 0.2, 0.4)
            for dw in (-0.2, -0.1, 0.0)
        ]
    if viability_class == "near_boundary":
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": dy, "half_width_delta": dw}
            for dx in (-0.5, 0.0, 0.5)
            for dy in (-0.2, 0.0, 0.2)
            for dw in (0.0, 0.1)
        ]
    center = _center_direction(relocated_body_y)
    return [
        {"body_longitudinal_delta": dx, "body_lateral_delta": center * dy, "half_width_delta": dw}
        for dx in (-2.0, -1.0)
        for dy in (0.0, 0.2, 0.4)
        for dw in (0.2, 0.4)
    ]


def _source_group(row: dict[str, Any], *, original_families: set[str]) -> str:
    family = source_family_signature(row)
    variant = str(row.get("variant", ""))
    if _bool_value(row.get("control_positive", False)) or variant in CONTROL_VARIANTS:
        return "control_diagnostic" if family in original_families else "control_neighbor"
    if family in original_families:
        return "original_source"
    return "neighbor_source"


def _calibration_score(row: dict[str, Any], *, source_group: str, viability_class: str, near_margin_high: float) -> float:
    normal_margin = _finite(row.get("normal_margin"))
    margin_gap = _finite(row.get("margin_gap"), 0.0)
    sequence_l2 = _finite(row.get("sequence_action_l2_mean"), 0.0)
    group_bonus = {"neighbor_source": 2.0, "original_source": -2.0, "control_diagnostic": -3.0, "control_neighbor": -4.0}.get(source_group, 0.0)
    class_bonus = {"near_boundary": 2.0, "too_hard": 1.0, "too_easy": 0.5}.get(viability_class, 0.0)
    if viability_class == "too_hard":
        margin_term = max(0.0, 1.0 + normal_margin) if math.isfinite(normal_margin) else 0.0
    elif viability_class == "near_boundary":
        margin_term = max(0.0, 1.0 - abs(normal_margin - 0.5 * near_margin_high) / max(near_margin_high, 1e-6))
    else:
        margin_term = max(0.0, min(normal_margin, 5.0) / 5.0) if math.isfinite(normal_margin) else 0.0
    return group_bonus + class_bonus + margin_term + max(0.0, margin_gap) / 0.02 + sequence_l2 / 0.10


def build_neighbor_viability_audit(
    *,
    actual_replay_rows: pd.DataFrame,
    history_positive_rows: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    near_margin_high: float = DEFAULT_NEAR_MARGIN_HIGH,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    if actual_replay_rows.empty:
        return pd.DataFrame()
    original_families = original_source_families(history_positive_rows)
    control_families = {source_family_signature(row) for row in control_positive_rows.to_dict("records")}
    audit_rows: list[dict[str, Any]] = []
    for rank, row in enumerate(actual_replay_rows.to_dict("records")):
        source_group = _source_group(row, original_families=original_families)
        normal_success = _bool_value(row.get("normal_success", False))
        normal_margin = _finite(row.get("normal_margin"))
        margin_gap = _finite(row.get("margin_gap"), 0.0)
        sequence_l2 = _finite(row.get("sequence_action_l2_mean"), 0.0)
        viability_class = classify_viability(
            normal_success=normal_success,
            normal_margin=normal_margin,
            margin_gap=margin_gap,
            near_margin_high=near_margin_high,
        )
        history_variant = str(row.get("variant", "")) in WARMUP_HISTORY_VARIANTS
        calibration_candidate = bool(
            source_group == "neighbor_source"
            and history_variant
            and sequence_l2 >= float(min_sequence_action_l2)
            and math.isfinite(normal_margin)
        )
        family = source_family_signature(row)
        audit_rows.append(
            {
                "viability_audit_rank": int(rank),
                "source_group": source_group,
                "viability_class": viability_class,
                "calibration_candidate": calibration_candidate,
                "original_source_family": bool(family in original_families),
                "control_source_family": bool(family in control_families),
                "source_family_signature": family,
                "selected_index": int(_finite(row.get("selected_index"), rank)),
                "source_index": int(_finite(row.get("source_index"), rank)),
                "seed": int(_finite(row.get("seed"), 0)),
                "reveal_step": int(_finite(row.get("reveal_step"), _source_step(row))),
                "source_step": int(_source_step(row)),
                "candidate_step": int(_source_step(row)),
                "candidate_step_column": "source_step",
                "preferred_fault": str(row.get("preferred_fault", "")),
                "wrong_fault": str(row.get("wrong_fault", "")),
                "capability_pair": str(row.get("capability_pair", "")),
                "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
                "variant": str(row.get("variant", "")),
                "normal_success": normal_success,
                "variant_success": bool(_bool_value(row.get("variant_success", False))),
                "normal_margin": normal_margin,
                "variant_margin": _finite(row.get("variant_margin")),
                "margin_gap": margin_gap,
                "sequence_action_l2_mean": sequence_l2,
                "source_body_x": _finite(row.get("source_body_x")),
                "source_body_y": _finite(row.get("source_body_y")),
                "source_half_width": _finite(row.get("source_half_width")),
                "relocated_body_x": _finite(row.get("relocated_body_x"), _finite(row.get("raw_relocated_body_x"))),
                "relocated_body_y": _finite(row.get("relocated_body_y")),
                "relocated_half_width": _finite(row.get("relocated_half_width"), _finite(row.get("raw_relocated_half_width"))),
                "calibration_score": _calibration_score(row, source_group=source_group, viability_class=viability_class, near_margin_high=near_margin_high),
            }
        )
    return pd.DataFrame(audit_rows)


def _base_offsets(row: dict[str, Any]) -> dict[str, float]:
    source_body_x = _finite(row.get("source_body_x"))
    source_body_y = _finite(row.get("source_body_y"))
    source_half_width = _finite(row.get("source_half_width"))
    relocated_x = _finite(row.get("relocated_body_x"), _finite(row.get("raw_relocated_body_x")))
    relocated_y = _finite(row.get("relocated_body_y"))
    relocated_width = _finite(row.get("relocated_half_width"), _finite(row.get("raw_relocated_half_width")))
    return {
        "body_longitudinal_offset": relocated_x - source_body_x,
        "body_lateral_offset": relocated_y - source_body_y,
        "half_width_inflation": relocated_width - source_half_width,
    }


def _proposal_from_delta(row: dict[str, Any], delta: dict[str, float], *, rank: int) -> dict[str, Any]:
    base = _base_offsets(row)
    source_half_width = _finite(row.get("source_half_width"))
    half_width_floor = DEFAULT_MIN_HALF_WIDTH - source_half_width
    body_longitudinal_offset = base["body_longitudinal_offset"] + float(delta["body_longitudinal_delta"])
    body_lateral_offset = base["body_lateral_offset"] + float(delta["body_lateral_delta"])
    half_width_inflation = max(half_width_floor, base["half_width_inflation"] + float(delta["half_width_delta"]))
    source_step = int(_source_step(row))
    output = {
        "calibration_rank": int(rank),
        "source_group": str(row.get("source_group", "")),
        "viability_class": str(row.get("viability_class", "")),
        "calibration_candidate": bool(_bool_value(row.get("calibration_candidate", False))),
        "viability_audit_rank": int(_finite(row.get("viability_audit_rank"), rank)),
        "selected_index": int(_finite(row.get("selected_index"), rank)),
        "source_index": int(_finite(row.get("source_index"), rank)),
        "seed": int(_finite(row.get("seed"), 0)),
        "reveal_step": int(_finite(row.get("reveal_step"), source_step)),
        "source_step": int(source_step),
        "candidate_step": int(source_step),
        "candidate_step_column": "source_step",
        "preferred_fault": str(row.get("preferred_fault", "")),
        "wrong_fault": str(row.get("wrong_fault", "")),
        "capability_pair": str(row.get("capability_pair", "")),
        "preferred_reveal_bucket": str(row.get("preferred_reveal_bucket", "")),
        "variant": str(row.get("variant", "")),
        "source_family_signature": str(row.get("source_family_signature", "")),
        "normal_success": bool(_bool_value(row.get("normal_success", False))),
        "normal_margin": _finite(row.get("normal_margin")),
        "variant_success": bool(_bool_value(row.get("variant_success", False))),
        "variant_margin": _finite(row.get("variant_margin")),
        "margin_gap": _finite(row.get("margin_gap"), 0.0),
        "sequence_action_l2_mean": _finite(row.get("sequence_action_l2_mean"), 0.0),
        "calibration_score": _finite(row.get("calibration_score"), 0.0),
        "source_body_x": _finite(row.get("source_body_x")),
        "source_body_y": _finite(row.get("source_body_y")),
        "source_half_width": source_half_width,
        "base_body_longitudinal_offset": base["body_longitudinal_offset"],
        "base_body_lateral_offset": base["body_lateral_offset"],
        "base_half_width_inflation": base["half_width_inflation"],
        "body_longitudinal_delta": float(delta["body_longitudinal_delta"]),
        "body_lateral_delta": float(delta["body_lateral_delta"]),
        "half_width_delta": float(delta["half_width_delta"]),
        "body_longitudinal_offset": float(body_longitudinal_offset),
        "body_lateral_offset": float(body_lateral_offset),
        "half_width_inflation": float(half_width_inflation),
    }
    output["neighbor_viability_key"] = "|".join(
        str(output[key])
        for key in (
            "source_family_signature",
            "variant",
            "viability_class",
            "body_longitudinal_offset",
            "body_lateral_offset",
            "half_width_inflation",
        )
    )
    return output


def generate_neighbor_viability_proposals(
    viability_audit: pd.DataFrame,
    *,
    include_original_diagnostics: bool = True,
    include_control_diagnostics: bool = True,
) -> pd.DataFrame:
    if viability_audit.empty:
        return pd.DataFrame()
    source_rows = viability_audit[
        viability_audit["calibration_candidate"].map(_bool_value)
        | (include_original_diagnostics & (viability_audit["source_group"].astype(str) == "original_source"))
        | (include_control_diagnostics & (viability_audit["source_group"].astype(str) == "control_diagnostic"))
    ].copy()
    proposals: list[dict[str, Any]] = []
    for _, row in source_rows.iterrows():
        row_dict = row.to_dict()
        for delta in calibration_delta_grid(
            str(row_dict.get("viability_class", "")),
            relocated_body_y=_finite(row_dict.get("relocated_body_y")),
        ):
            proposals.append(_proposal_from_delta(row_dict, delta, rank=len(proposals)))
    return pd.DataFrame(proposals)


def select_neighbor_viability_candidates(
    proposals: pd.DataFrame,
    *,
    max_candidates: int = 192,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 24,
    per_reveal_bucket_cap: int = 24,
    per_viability_class_cap: int = 64,
    per_variant_cap: int = 64,
    original_source_cap: int = 8,
    control_diagnostic_cap: int = 24,
) -> pd.DataFrame:
    if proposals.empty:
        return proposals.copy()
    frame = proposals.copy()
    group_priority = {"neighbor_source": 0, "original_source": 1, "control_diagnostic": 2, "control_neighbor": 3}
    class_priority = {"near_boundary": 0, "too_hard": 1, "too_easy": 2}
    frame["_group_priority"] = frame["source_group"].map(group_priority).fillna(9).astype(int)
    frame["_class_priority"] = frame["viability_class"].map(class_priority).fillna(9).astype(int)
    frame = frame.sort_values(
        ["_group_priority", "_class_priority", "calibration_score", "sequence_action_l2_mean", "calibration_rank"],
        ascending=[True, True, False, False, True],
    )
    counters: dict[str, Counter] = {
        "seed": Counter(),
        "pair": Counter(),
        "bucket": Counter(),
        "class": Counter(),
        "variant": Counter(),
        "group": Counter(),
    }
    seen_keys: set[str] = set()
    selected: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        key = str(row["neighbor_viability_key"])
        if key in seen_keys:
            continue
        group = str(row["source_group"])
        seed = str(row["seed"])
        pair = str(row["capability_pair"])
        bucket = str(row["preferred_reveal_bucket"])
        klass = str(row["viability_class"])
        variant = str(row["variant"])
        if per_seed_cap > 0 and counters["seed"][seed] >= per_seed_cap:
            continue
        if per_capability_pair_cap > 0 and counters["pair"][pair] >= per_capability_pair_cap:
            continue
        if per_reveal_bucket_cap > 0 and counters["bucket"][bucket] >= per_reveal_bucket_cap:
            continue
        if per_viability_class_cap > 0 and counters["class"][klass] >= per_viability_class_cap:
            continue
        if per_variant_cap > 0 and counters["variant"][variant] >= per_variant_cap:
            continue
        if group == "original_source" and original_source_cap >= 0 and counters["group"][group] >= original_source_cap:
            continue
        if group.startswith("control") and control_diagnostic_cap >= 0 and counters["group"][group] >= control_diagnostic_cap:
            continue
        output = row.drop(labels=[c for c in ("_group_priority", "_class_priority") if c in row.index]).to_dict()
        output["selected_calibration_rank"] = len(selected)
        selected.append(output)
        seen_keys.add(key)
        counters["seed"][seed] += 1
        counters["pair"][pair] += 1
        counters["bucket"][bucket] += 1
        counters["class"][klass] += 1
        counters["variant"][variant] += 1
        counters["group"][group] += 1
        if max_candidates > 0 and len(selected) >= max_candidates:
            break
    return pd.DataFrame(selected)


def build_neighbor_viability_summary(
    *,
    actual_replay_rows: pd.DataFrame,
    history_positive_rows: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    viability_audit: pd.DataFrame,
    proposals: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    audit_group_counts = viability_audit["source_group"].value_counts().to_dict() if "source_group" in viability_audit else {}
    audit_class_counts = viability_audit["viability_class"].value_counts().to_dict() if "viability_class" in viability_audit else {}
    selected_group_counts = selected["source_group"].value_counts().to_dict() if "source_group" in selected else {}
    selected_class_counts = selected["viability_class"].value_counts().to_dict() if "viability_class" in selected else {}
    return {
        "run_type": "neighbor_viability_calibration",
        "actual_replay_rows": int(len(actual_replay_rows)),
        "history_positive_rows": int(len(history_positive_rows)),
        "control_positive_rows": int(len(control_positive_rows)),
        "viability_audit_rows": int(len(viability_audit)),
        "calibration_candidate_rows": int(viability_audit["calibration_candidate"].map(_bool_value).sum() if "calibration_candidate" in viability_audit else 0),
        "proposal_rows": int(len(proposals)),
        "selected_candidate_rows": int(len(selected)),
        "selected_unique_neighbor_viability_keys": int(selected["neighbor_viability_key"].nunique() if "neighbor_viability_key" in selected else 0),
        "selected_duplicate_neighbor_viability_key_rows": int(
            len(selected) - selected["neighbor_viability_key"].nunique()
            if "neighbor_viability_key" in selected
            else 0
        ),
        "audit_source_group_counts": {str(k): int(v) for k, v in audit_group_counts.items()},
        "audit_viability_class_counts": {str(k): int(v) for k, v in audit_class_counts.items()},
        "selected_source_group_counts": {str(k): int(v) for k, v in selected_group_counts.items()},
        "selected_viability_class_counts": {str(k): int(v) for k, v in selected_class_counts.items()},
        "selected_diversity": source_diversity(selected.to_dict("records") if not selected.empty else []),
        "candidate_step_column": "source_step",
        "source_preflight_started": False,
        "replay_started": False,
        "outcome_interventions_started": False,
        "training_started": False,
        "evaluation_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "training_corpus_exported": False,
        "actor_input_contract_changed": False,
    }


def run_neighbor_viability_generation(
    *,
    actual_replay_rows: Path,
    history_positive_rows: Path,
    control_positive_rows: Path,
    run_dir: Path,
    max_candidates: int = 192,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 24,
    per_reveal_bucket_cap: int = 24,
    per_viability_class_cap: int = 64,
    per_variant_cap: int = 64,
    original_source_cap: int = 8,
    control_diagnostic_cap: int = 24,
) -> dict[str, Any]:
    actual = pd.read_csv(actual_replay_rows)
    history_positive = pd.read_csv(history_positive_rows)
    controls = pd.read_csv(control_positive_rows)
    audit = build_neighbor_viability_audit(
        actual_replay_rows=actual,
        history_positive_rows=history_positive,
        control_positive_rows=controls,
    )
    proposals = generate_neighbor_viability_proposals(audit)
    selected = select_neighbor_viability_candidates(
        proposals,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_viability_class_cap=per_viability_class_cap,
        per_variant_cap=per_variant_cap,
        original_source_cap=original_source_cap,
        control_diagnostic_cap=control_diagnostic_cap,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "neighbor_viability_audit_rows.csv", audit.to_dict("records") if not audit.empty else [])
    write_csv_rows(run_dir / "neighbor_viability_proposal_rows.csv", proposals.to_dict("records") if not proposals.empty else [])
    write_csv_rows(run_dir / "neighbor_viability_candidate_rows.csv", selected.to_dict("records") if not selected.empty else [])
    summary = build_neighbor_viability_summary(
        actual_replay_rows=actual,
        history_positive_rows=history_positive,
        control_positive_rows=controls,
        viability_audit=audit,
        proposals=proposals,
        selected=selected,
    )
    summary["actual_replay_rows_csv"] = str(actual_replay_rows)
    summary["history_positive_rows_csv"] = str(history_positive_rows)
    summary["control_positive_rows_csv"] = str(control_positive_rows)
    summary["neighbor_viability_audit_rows_csv"] = str(run_dir / "neighbor_viability_audit_rows.csv")
    summary["neighbor_viability_proposal_rows_csv"] = str(run_dir / "neighbor_viability_proposal_rows.csv")
    summary["neighbor_viability_candidate_rows_csv"] = str(run_dir / "neighbor_viability_candidate_rows.csv")
    summary["summary_json"] = str(run_dir / "summary.json")
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-replay-rows", type=Path, required=True)
    parser.add_argument("--history-positive-rows", type=Path, required=True)
    parser.add_argument("--control-positive-rows", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=192)
    parser.add_argument("--per-seed-cap", type=int, default=24)
    parser.add_argument("--per-capability-pair-cap", type=int, default=24)
    parser.add_argument("--per-reveal-bucket-cap", type=int, default=24)
    parser.add_argument("--per-viability-class-cap", type=int, default=64)
    parser.add_argument("--per-variant-cap", type=int, default=64)
    parser.add_argument("--original-source-cap", type=int, default=8)
    parser.add_argument("--control-diagnostic-cap", type=int, default=24)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="neighbor_viability_calibration")
    summary = run_neighbor_viability_generation(
        actual_replay_rows=args.actual_replay_rows,
        history_positive_rows=args.history_positive_rows,
        control_positive_rows=args.control_positive_rows,
        run_dir=run_dir,
        max_candidates=args.max_candidates,
        per_seed_cap=args.per_seed_cap,
        per_capability_pair_cap=args.per_capability_pair_cap,
        per_reveal_bucket_cap=args.per_reveal_bucket_cap,
        per_viability_class_cap=args.per_viability_class_cap,
        per_variant_cap=args.per_variant_cap,
        original_source_cap=args.original_source_cap,
        control_diagnostic_cap=args.control_diagnostic_cap,
    )
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"viability_audit_rows={summary['viability_audit_rows']}")
    print(f"proposal_rows={summary['proposal_rows']}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")


if __name__ == "__main__":
    main()
