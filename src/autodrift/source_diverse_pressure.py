"""Source-diverse pressure candidate generator for local positive surfaces."""

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


DEFAULT_BOUNDARY_MARGIN_HIGH = 1.0
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


def source_variant_signature(row: dict[str, Any]) -> str:
    return "|".join((source_family_signature(row), str(row.get("variant", ""))))


def history_anchor_rows(history_positive_rows: pd.DataFrame) -> pd.DataFrame:
    if history_positive_rows.empty:
        return history_positive_rows.copy()
    frame = history_positive_rows.copy()
    if "history_positive" in frame:
        frame = frame[frame["history_positive"].map(_bool_value)]
    if "control_positive" in frame:
        frame = frame[~frame["control_positive"].map(_bool_value)]
    return frame.reset_index(drop=True)


def _source_group(
    row: dict[str, Any],
    *,
    anchor_families: set[str],
    control_families: set[str],
) -> str:
    family = source_family_signature(row)
    variant = str(row.get("variant", ""))
    if _bool_value(row.get("control_positive", False)) or variant in CONTROL_VARIANTS:
        return "control_diagnostic" if family in anchor_families or family in control_families else "control_neighbor"
    if family in anchor_families:
        return "original_source"
    return "neighbor_source"


def _near_boundary_score(normal_margin: float, *, boundary_margin_high: float) -> float:
    if not math.isfinite(normal_margin):
        return 0.0
    if normal_margin < 0.0:
        return max(0.0, 1.0 + normal_margin)
    return max(0.0, 1.0 - abs(normal_margin - boundary_margin_high) / max(boundary_margin_high, 1e-6))


def _pressure_score(
    row: dict[str, Any],
    *,
    source_group: str,
    boundary_margin_high: float,
) -> float:
    normal_margin = _finite(row.get("normal_margin"))
    margin_gap = _finite(row.get("margin_gap"), 0.0)
    sequence_l2 = _finite(row.get("sequence_action_l2_mean"), 0.0)
    group_bonus = {
        "neighbor_source": 1.0,
        "original_source": -1.0,
        "control_diagnostic": -2.0,
        "control_neighbor": -3.0,
    }.get(source_group, 0.0)
    return (
        group_bonus
        + _near_boundary_score(normal_margin, boundary_margin_high=boundary_margin_high)
        + max(0.0, margin_gap) / 0.02
        + sequence_l2 / 0.10
    )


def build_source_pressure_audit(
    *,
    actual_replay_rows: pd.DataFrame,
    history_positive_rows: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH,
    min_sequence_action_l2: float = DEFAULT_MIN_SEQUENCE_ACTION_L2,
) -> pd.DataFrame:
    anchors = history_anchor_rows(history_positive_rows)
    if actual_replay_rows.empty or anchors.empty:
        return pd.DataFrame()
    live_relocation_keys = {str(row.get("relocation_key", "")) for row in anchors.to_dict("records")}
    anchor_families = {source_family_signature(row) for row in anchors.to_dict("records")}
    control_families = {source_family_signature(row) for row in control_positive_rows.to_dict("records")}
    audit_rows: list[dict[str, Any]] = []
    for source_rank, row in enumerate(actual_replay_rows.to_dict("records")):
        relocation_key = str(row.get("relocation_key", ""))
        if relocation_key not in live_relocation_keys:
            continue
        source_group = _source_group(row, anchor_families=anchor_families, control_families=control_families)
        sequence_l2 = _finite(row.get("sequence_action_l2_mean"), 0.0)
        normal_margin = _finite(row.get("normal_margin"))
        margin_gap = _finite(row.get("margin_gap"), 0.0)
        history_variant = str(row.get("variant", "")) in WARMUP_HISTORY_VARIANTS
        pressure_candidate = bool(
            source_group == "neighbor_source"
            and history_variant
            and sequence_l2 >= float(min_sequence_action_l2)
            and math.isfinite(normal_margin)
        )
        audit_rows.append(
            {
                "source_audit_rank": int(source_rank),
                "source_group": source_group,
                "pressure_candidate": pressure_candidate,
                "source_family_signature": source_family_signature(row),
                "source_variant_signature": source_variant_signature(row),
                "relocation_key": relocation_key,
                "selected_index": int(_finite(row.get("selected_index"), source_rank)),
                "source_index": int(_finite(row.get("source_index"), source_rank)),
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
                "normal_success": bool(_bool_value(row.get("normal_success", False))),
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
                "pressure_score": _pressure_score(row, source_group=source_group, boundary_margin_high=boundary_margin_high),
            }
        )
    return pd.DataFrame(audit_rows)


def pressure_delta_grid(normal_margin: float, *, relocated_body_y: float, boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH) -> list[dict[str, float]]:
    if math.isfinite(normal_margin) and 0.0 <= normal_margin <= boundary_margin_high:
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": dy, "half_width_delta": dw}
            for dx in (-0.5, 0.0, 0.5)
            for dy in (-0.2, 0.0, 0.2)
            for dw in (0.0, 0.1, 0.2)
        ]
    direction = 0.0
    if math.isfinite(relocated_body_y) and abs(relocated_body_y) > 1e-9:
        direction = -1.0 if relocated_body_y > 0.0 else 1.0
    if math.isfinite(normal_margin) and normal_margin > boundary_margin_high:
        return [
            {"body_longitudinal_delta": dx, "body_lateral_delta": direction * dy, "half_width_delta": dw}
            for dx in (-2.0, -1.0)
            for dy in (0.0, 0.2, 0.4)
            for dw in (0.2, 0.4)
        ]
    return [
        {"body_longitudinal_delta": dx, "body_lateral_delta": -direction * dy, "half_width_delta": dw}
        for dx in (1.0, 2.0)
        for dy in (0.0, 0.2)
        for dw in (-0.1, 0.0)
    ]


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
        "pressure_rank": int(rank),
        "source_group": str(row.get("source_group", "")),
        "pressure_candidate": bool(_bool_value(row.get("pressure_candidate", False))),
        "source_audit_rank": int(_finite(row.get("source_audit_rank"), rank)),
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
        "source_variant_signature": str(row.get("source_variant_signature", "")),
        "relocation_key": str(row.get("relocation_key", "")),
        "normal_success": bool(_bool_value(row.get("normal_success", False))),
        "normal_margin": _finite(row.get("normal_margin")),
        "variant_success": bool(_bool_value(row.get("variant_success", False))),
        "variant_margin": _finite(row.get("variant_margin")),
        "margin_gap": _finite(row.get("margin_gap"), 0.0),
        "sequence_action_l2_mean": _finite(row.get("sequence_action_l2_mean"), 0.0),
        "pressure_score": _finite(row.get("pressure_score"), 0.0),
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
    output["source_diverse_pressure_key"] = "|".join(
        str(output[key])
        for key in (
            "source_family_signature",
            "variant",
            "relocation_key",
            "body_longitudinal_offset",
            "body_lateral_offset",
            "half_width_inflation",
        )
    )
    return output


def generate_source_diverse_pressure_proposals(
    source_audit: pd.DataFrame,
    *,
    include_original_diagnostics: bool = True,
    include_control_diagnostics: bool = True,
    boundary_margin_high: float = DEFAULT_BOUNDARY_MARGIN_HIGH,
) -> pd.DataFrame:
    if source_audit.empty:
        return pd.DataFrame()
    source_rows = source_audit[
        source_audit["pressure_candidate"].map(_bool_value)
        | (include_original_diagnostics & (source_audit["source_group"].astype(str) == "original_source"))
        | (include_control_diagnostics & (source_audit["source_group"].astype(str) == "control_diagnostic"))
    ].copy()
    proposals: list[dict[str, Any]] = []
    for _, row in source_rows.iterrows():
        row_dict = row.to_dict()
        for delta in pressure_delta_grid(
            _finite(row_dict.get("normal_margin")),
            relocated_body_y=_finite(row_dict.get("relocated_body_y")),
            boundary_margin_high=boundary_margin_high,
        ):
            proposals.append(_proposal_from_delta(row_dict, delta, rank=len(proposals)))
    return pd.DataFrame(proposals)


def select_source_diverse_pressure_candidates(
    proposals: pd.DataFrame,
    *,
    max_candidates: int = 192,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 24,
    per_reveal_bucket_cap: int = 24,
    per_relocation_key_cap: int = 32,
    per_variant_cap: int = 64,
    original_source_cap: int = 12,
    control_diagnostic_cap: int = 32,
) -> pd.DataFrame:
    if proposals.empty:
        return proposals.copy()
    frame = proposals.copy()
    group_priority = {"neighbor_source": 0, "original_source": 1, "control_diagnostic": 2, "control_neighbor": 3}
    frame["_group_priority"] = frame["source_group"].map(group_priority).fillna(9).astype(int)
    frame = frame.sort_values(
        ["_group_priority", "pressure_score", "sequence_action_l2_mean", "pressure_rank"],
        ascending=[True, False, False, True],
    )
    counts: dict[str, Counter] = {
        "seed": Counter(),
        "pair": Counter(),
        "bucket": Counter(),
        "relocation": Counter(),
        "variant": Counter(),
        "group": Counter(),
    }
    seen_keys: set[str] = set()
    selected: list[dict[str, Any]] = []
    for _, row in frame.iterrows():
        key = str(row["source_diverse_pressure_key"])
        if key in seen_keys:
            continue
        group = str(row["source_group"])
        seed = str(row["seed"])
        pair = str(row["capability_pair"])
        bucket = str(row["preferred_reveal_bucket"])
        relocation = str(row["relocation_key"])
        variant = str(row["variant"])
        if per_seed_cap > 0 and counts["seed"][seed] >= per_seed_cap:
            continue
        if per_capability_pair_cap > 0 and counts["pair"][pair] >= per_capability_pair_cap:
            continue
        if per_reveal_bucket_cap > 0 and counts["bucket"][bucket] >= per_reveal_bucket_cap:
            continue
        if per_relocation_key_cap > 0 and counts["relocation"][relocation] >= per_relocation_key_cap:
            continue
        if per_variant_cap > 0 and counts["variant"][variant] >= per_variant_cap:
            continue
        if group == "original_source" and original_source_cap >= 0 and counts["group"][group] >= original_source_cap:
            continue
        if group.startswith("control") and control_diagnostic_cap >= 0 and counts["group"][group] >= control_diagnostic_cap:
            continue
        output = row.drop(labels=[c for c in ("_group_priority",) if c in row.index]).to_dict()
        output["selected_pressure_rank"] = len(selected)
        selected.append(output)
        seen_keys.add(key)
        counts["seed"][seed] += 1
        counts["pair"][pair] += 1
        counts["bucket"][bucket] += 1
        counts["relocation"][relocation] += 1
        counts["variant"][variant] += 1
        counts["group"][group] += 1
        if max_candidates > 0 and len(selected) >= max_candidates:
            break
    return pd.DataFrame(selected)


def build_source_diverse_pressure_summary(
    *,
    actual_replay_rows: pd.DataFrame,
    anchors: pd.DataFrame,
    control_positive_rows: pd.DataFrame,
    candidate_pool: pd.DataFrame,
    source_audit: pd.DataFrame,
    proposals: pd.DataFrame,
    selected: pd.DataFrame,
) -> dict[str, Any]:
    selected_group_counts = selected["source_group"].value_counts().to_dict() if "source_group" in selected else {}
    audit_group_counts = source_audit["source_group"].value_counts().to_dict() if "source_group" in source_audit else {}
    proposal_group_counts = proposals["source_group"].value_counts().to_dict() if "source_group" in proposals else {}
    return {
        "run_type": "source_diverse_pressure",
        "actual_replay_rows": int(len(actual_replay_rows)),
        "history_positive_anchor_rows": int(len(anchors)),
        "control_positive_rows": int(len(control_positive_rows)),
        "candidate_pool_rows": int(len(candidate_pool)),
        "source_audit_rows": int(len(source_audit)),
        "pressure_candidate_source_rows": int(source_audit["pressure_candidate"].map(_bool_value).sum() if "pressure_candidate" in source_audit else 0),
        "proposal_rows": int(len(proposals)),
        "selected_candidate_rows": int(len(selected)),
        "selected_unique_pressure_keys": int(selected["source_diverse_pressure_key"].nunique() if "source_diverse_pressure_key" in selected else 0),
        "selected_duplicate_pressure_key_rows": int(
            len(selected) - selected["source_diverse_pressure_key"].nunique()
            if "source_diverse_pressure_key" in selected
            else 0
        ),
        "audit_source_group_counts": {str(k): int(v) for k, v in audit_group_counts.items()},
        "proposal_source_group_counts": {str(k): int(v) for k, v in proposal_group_counts.items()},
        "selected_source_group_counts": {str(k): int(v) for k, v in selected_group_counts.items()},
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


def run_source_diverse_pressure_generation(
    *,
    actual_replay_rows: Path,
    history_positive_rows: Path,
    control_positive_rows: Path,
    candidate_pool: Path,
    run_dir: Path,
    max_candidates: int = 192,
    per_seed_cap: int = 24,
    per_capability_pair_cap: int = 24,
    per_reveal_bucket_cap: int = 24,
    per_relocation_key_cap: int = 32,
    per_variant_cap: int = 64,
    original_source_cap: int = 12,
    control_diagnostic_cap: int = 32,
) -> dict[str, Any]:
    actual = pd.read_csv(actual_replay_rows)
    history_positive = pd.read_csv(history_positive_rows)
    controls = pd.read_csv(control_positive_rows)
    pool = pd.read_csv(candidate_pool)
    anchors = history_anchor_rows(history_positive)
    source_audit = build_source_pressure_audit(
        actual_replay_rows=actual,
        history_positive_rows=anchors,
        control_positive_rows=controls,
    )
    proposals = generate_source_diverse_pressure_proposals(source_audit)
    selected = select_source_diverse_pressure_candidates(
        proposals,
        max_candidates=max_candidates,
        per_seed_cap=per_seed_cap,
        per_capability_pair_cap=per_capability_pair_cap,
        per_reveal_bucket_cap=per_reveal_bucket_cap,
        per_relocation_key_cap=per_relocation_key_cap,
        per_variant_cap=per_variant_cap,
        original_source_cap=original_source_cap,
        control_diagnostic_cap=control_diagnostic_cap,
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    write_csv_rows(run_dir / "source_diverse_pressure_anchor_rows.csv", anchors.to_dict("records") if not anchors.empty else [])
    write_csv_rows(run_dir / "source_diverse_pressure_source_audit.csv", source_audit.to_dict("records") if not source_audit.empty else [])
    write_csv_rows(run_dir / "source_diverse_pressure_proposal_rows.csv", proposals.to_dict("records") if not proposals.empty else [])
    write_csv_rows(run_dir / "source_diverse_pressure_candidate_rows.csv", selected.to_dict("records") if not selected.empty else [])
    summary = build_source_diverse_pressure_summary(
        actual_replay_rows=actual,
        anchors=anchors,
        control_positive_rows=controls,
        candidate_pool=pool,
        source_audit=source_audit,
        proposals=proposals,
        selected=selected,
    )
    summary["actual_replay_rows_csv"] = str(actual_replay_rows)
    summary["history_positive_rows_csv"] = str(history_positive_rows)
    summary["control_positive_rows_csv"] = str(control_positive_rows)
    summary["candidate_pool_csv"] = str(candidate_pool)
    summary["source_diverse_pressure_anchor_rows_csv"] = str(run_dir / "source_diverse_pressure_anchor_rows.csv")
    summary["source_diverse_pressure_source_audit_csv"] = str(run_dir / "source_diverse_pressure_source_audit.csv")
    summary["source_diverse_pressure_proposal_rows_csv"] = str(run_dir / "source_diverse_pressure_proposal_rows.csv")
    summary["source_diverse_pressure_candidate_rows_csv"] = str(run_dir / "source_diverse_pressure_candidate_rows.csv")
    summary["summary_json"] = str(run_dir / "summary.json")
    write_json(run_dir / "summary.json", summary)
    return summary


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--actual-replay-rows", type=Path, required=True)
    parser.add_argument("--history-positive-rows", type=Path, required=True)
    parser.add_argument("--control-positive-rows", type=Path, required=True)
    parser.add_argument("--candidate-pool", type=Path, required=True)
    parser.add_argument("--max-candidates", type=int, default=192)
    parser.add_argument("--per-seed-cap", type=int, default=24)
    parser.add_argument("--per-capability-pair-cap", type=int, default=24)
    parser.add_argument("--per-reveal-bucket-cap", type=int, default=24)
    parser.add_argument("--per-relocation-key-cap", type=int, default=32)
    parser.add_argument("--per-variant-cap", type=int, default=64)
    parser.add_argument("--original-source-cap", type=int, default=12)
    parser.add_argument("--control-diagnostic-cap", type=int, default=32)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="source_diverse_pressure")
    summary = run_source_diverse_pressure_generation(
        actual_replay_rows=args.actual_replay_rows,
        history_positive_rows=args.history_positive_rows,
        control_positive_rows=args.control_positive_rows,
        candidate_pool=args.candidate_pool,
        run_dir=run_dir,
        max_candidates=args.max_candidates,
        per_seed_cap=args.per_seed_cap,
        per_capability_pair_cap=args.per_capability_pair_cap,
        per_reveal_bucket_cap=args.per_reveal_bucket_cap,
        per_relocation_key_cap=args.per_relocation_key_cap,
        per_variant_cap=args.per_variant_cap,
        original_source_cap=args.original_source_cap,
        control_diagnostic_cap=args.control_diagnostic_cap,
    )
    print(f"summary_json={run_dir / 'summary.json'}")
    print(f"source_audit_rows={summary['source_audit_rows']}")
    print(f"proposal_rows={summary['proposal_rows']}")
    print(f"selected_candidate_rows={summary['selected_candidate_rows']}")


if __name__ == "__main__":
    main()
