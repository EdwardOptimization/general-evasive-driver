"""Export a contour-aware candidate corpus package without training artifacts."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_materialization import CLEAN_LABEL
from autodrift.temporal_active_set_anchor_sensitivity_miner import _max_share


DEFAULT_CANDIDATE_ROWS = Path("runs/m1612_contour_aware_candidate_materialization/candidate_rows.csv")
DEFAULT_DIAGNOSTIC_ROWS = Path("runs/m1612_contour_aware_candidate_materialization/diagnostic_guardrail_rows.csv")
DEFAULT_RUN_DIR = Path("runs/m1615_contour_aware_candidate_corpus")
POSITIVE_ROLE = "positive_candidate"
DIAGNOSTIC_ROLE = "diagnostic_guardrail"
CORPUS_METADATA = {
    "public_proof_artifact": True,
    "private_holdout_used": False,
    "paper_level_claim_supported": False,
    "level3_self_id_claim_supported": False,
    "training_ready": False,
    "requires_export_audit": True,
    "requires_objective_design_before_training": True,
    "positive_candidate_default_weight": 1.0,
    "diagnostic_guardrail_training_weight": 0.0,
}
FORBIDDEN_GUARDRAILS = {
    "training_corpus_exported": False,
    "loss_constructed": False,
    "objective_constructed": False,
    "training_started": False,
    "evaluation_started": False,
    "replay_started": False,
    "history_interventions_executed": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
}


def _source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("source_edge", "")) for row in rows if str(row.get("source_edge", "")))


def _ids_unique(rows: Sequence[Mapping[str, Any]]) -> bool:
    ids = [str(row.get("pair_id", "")) for row in rows]
    return len(ids) == len(set(ids))


def _with_role(rows: Sequence[Mapping[str, Any]], *, role: str, role_weight: float) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["corpus_role"] = role
        item["role_weight"] = role_weight
        item["public_proof_artifact"] = True
        item["training_ready"] = False
        output.append(item)
    return output


def _metadata_complete(manifest: Mapping[str, Any]) -> bool:
    return (
        bool(manifest.get("public_proof_artifact")) is True
        and bool(manifest.get("private_holdout_used")) is False
        and bool(manifest.get("paper_level_claim_supported")) is False
        and bool(manifest.get("level3_self_id_claim_supported")) is False
        and bool(manifest.get("training_ready")) is False
        and bool(manifest.get("requires_export_audit")) is True
        and bool(manifest.get("requires_objective_design_before_training")) is True
    )


def role_summary(positive_rows: Sequence[Mapping[str, Any]], diagnostic_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "corpus_role": POSITIVE_ROLE,
            "row_count": len(positive_rows),
            "role_weight": 1.0,
            "training_role": "candidate_only",
        },
        {
            "corpus_role": DIAGNOSTIC_ROLE,
            "row_count": len(diagnostic_rows),
            "role_weight": 0.0,
            "training_role": "guardrail_only",
        },
    ]


def build_manifest(positive_rows: Sequence[Mapping[str, Any]], diagnostic_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "result_class": "contour_aware_candidate_corpus_package",
        "positive_candidate_count": len(positive_rows),
        "diagnostic_guardrail_count": len(diagnostic_rows),
        "roles": [POSITIVE_ROLE, DIAGNOSTIC_ROLE],
        **CORPUS_METADATA,
    }


def build_summary(
    positive_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    source_edge_counts = _source_edge_counts(positive_rows)
    positive_ids = {str(row.get("pair_id", "")) for row in positive_rows}
    diagnostic_ids = {str(row.get("pair_id", "")) for row in diagnostic_rows}
    diagnostic_rows_used_as_positive = bool(positive_ids & diagnostic_ids) or any(
        str(row.get("corpus_role", "")) == POSITIVE_ROLE for row in diagnostic_rows
    )
    positive_rows_all_clean = all(
        str(row.get("label", "")) == CLEAN_LABEL and str(row.get("m1602_label", "")) == CLEAN_LABEL
        for row in positive_rows
    )
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_candidate_corpus_export",
        "candidate_corpus_exported": True,
        "positive_candidate_count": len(positive_rows),
        "diagnostic_guardrail_count": len(diagnostic_rows),
        "positive_rows_all_clean": bool(positive_rows_all_clean),
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "candidate_pair_ids_unique": _ids_unique(positive_rows),
        "diagnostic_pair_ids_unique": _ids_unique(diagnostic_rows),
        "source_edge_count": len(source_edge_counts),
        "max_source_edge_share": _max_share(source_edge_counts),
        "public_proof_metadata_complete": _metadata_complete(manifest),
        "requires_export_audit": bool(manifest.get("requires_export_audit", False)),
        "requires_objective_design_before_training": bool(manifest.get("requires_objective_design_before_training", False)),
        "guardrail_violation_count": guardrail_violation_count,
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        bool(summary["candidate_corpus_exported"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["loss_constructed"])
        and not bool(summary["objective_constructed"])
        and int(summary["positive_candidate_count"]) == 39
        and int(summary["diagnostic_guardrail_count"]) == 232
        and bool(summary["positive_rows_all_clean"])
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and bool(summary["candidate_pair_ids_unique"])
        and bool(summary["diagnostic_pair_ids_unique"])
        and int(summary["source_edge_count"]) == 4
        and float(summary["max_source_edge_share"]) <= 0.35
        and bool(summary["public_proof_metadata_complete"])
        and bool(summary["requires_export_audit"])
        and bool(summary["requires_objective_design_before_training"])
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
    )
    summary["passes_evidence_quality_targets"] = bool(summary["passes_public_smoke_gates"])
    if not bool(summary["positive_rows_all_clean"]):
        null_class = "non_clean_positive_candidate_leakage"
    elif bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif not bool(summary["public_proof_metadata_complete"]):
        null_class = "metadata_incomplete"
    elif bool(summary["training_corpus_exported"]):
        null_class = "training_corpus_export_violation"
    elif bool(summary["loss_constructed"]) or bool(summary["objective_constructed"]):
        null_class = "objective_construction_violation"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_candidate_corpus_export_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    return summary


def run_contour_aware_candidate_corpus_export(
    output_dir: Path | str,
    *,
    candidate_rows: Path | str = DEFAULT_CANDIDATE_ROWS,
    diagnostic_rows: Path | str = DEFAULT_DIAGNOSTIC_ROWS,
) -> dict[str, Any]:
    """Export the candidate corpus package."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    positive_input_rows = read_csv_rows(candidate_rows)
    diagnostic_input_rows = read_csv_rows(diagnostic_rows)
    positive_rows = _with_role(positive_input_rows, role=POSITIVE_ROLE, role_weight=1.0)
    diagnostic_guardrail_rows = _with_role(diagnostic_input_rows, role=DIAGNOSTIC_ROLE, role_weight=0.0)
    manifest = build_manifest(positive_rows, diagnostic_guardrail_rows)
    summary = build_summary(positive_rows, diagnostic_guardrail_rows, manifest)
    write_csv_rows(output / "positive_candidate_rows.csv", positive_rows)
    write_csv_rows(output / "diagnostic_guardrail_rows.csv", diagnostic_guardrail_rows)
    write_json(output / "corpus_manifest.json", manifest)
    write_csv_rows(output / "role_summary.csv", role_summary(positive_rows, diagnostic_guardrail_rows))
    source_rows = []
    total = len(positive_rows)
    for edge, count in sorted(_source_edge_counts(positive_rows).items()):
        source_rows.append({"source_edge": edge, "positive_candidate_count": count, "share": count / total if total else 0.0})
    write_csv_rows(output / "source_edge_summary.csv", source_rows)
    guardrail_rows = [{"guardrail": "candidate_corpus_exported", "violated": False, "value": True}]
    guardrail_rows.extend({"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items())
    write_csv_rows(output / "guardrail_summary.csv", guardrail_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Export contour-aware candidate corpus package.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--candidate-rows", type=Path, default=DEFAULT_CANDIDATE_ROWS)
    parser.add_argument("--diagnostic-rows", type=Path, default=DEFAULT_DIAGNOSTIC_ROWS)
    args = parser.parse_args()
    summary = run_contour_aware_candidate_corpus_export(
        args.output_dir,
        candidate_rows=args.candidate_rows,
        diagnostic_rows=args.diagnostic_rows,
    )
    print(f"summary={args.output_dir / 'summary.json'}")
    print(f"positive_candidate_count={summary['positive_candidate_count']}")
    print(f"diagnostic_guardrail_count={summary['diagnostic_guardrail_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
