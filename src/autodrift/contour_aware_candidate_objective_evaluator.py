"""No-update evaluator for contour-aware candidate objective packages."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_candidate_corpus_export import DIAGNOSTIC_ROLE, POSITIVE_ROLE
from autodrift.contour_aware_candidate_materialization import CLEAN_LABEL
from autodrift.temporal_active_set_anchor_sensitivity_miner import _max_share


DEFAULT_CANDIDATE_RUN_DIR = Path("runs/m1615_contour_aware_candidate_corpus")
DEFAULT_CHECKPOINT = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt")
DEFAULT_RUN_DIR = Path("runs/m1619_contour_aware_candidate_objective_evaluator")
OBJECTIVE_MARGIN = 0.0
FORBIDDEN_GUARDRAILS = {
    "training_started": False,
    "ppo_used": False,
    "promoted": False,
    "private_holdout_used": False,
    "actor_input_contract_changed": False,
    "labels_enter_actor_input": False,
    "level3_self_id_claim_made": False,
    "training_corpus_exported": False,
    "loss_constructed": False,
    "objective_constructed": False,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _bool_text(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def _float(value: Any) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return output if math.isfinite(output) else float("nan")


def _softplus(value: float) -> float:
    if value > 40.0:
        return value
    if value < -40.0:
        return math.exp(value)
    return math.log1p(math.exp(value))


def _mean(values: Sequence[float]) -> float:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    return float(sum(finite) / len(finite)) if finite else float("nan")


def _all_finite(values: Sequence[float]) -> bool:
    return all(math.isfinite(float(value)) for value in values)


def _source_edge_counts(rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("source_edge", "")) for row in rows if str(row.get("source_edge", "")))


def _metadata_complete(manifest: Mapping[str, Any]) -> bool:
    return (
        bool(manifest.get("public_proof_artifact")) is True
        and bool(manifest.get("private_holdout_used")) is False
        and bool(manifest.get("paper_level_claim_supported")) is False
        and bool(manifest.get("level3_self_id_claim_supported")) is False
        and bool(manifest.get("training_ready")) is False
        and bool(manifest.get("requires_objective_design_before_training")) is True
    )


def positive_objective_rows(rows: Sequence[Mapping[str, Any]], *, margin: float = OBJECTIVE_MARGIN) -> list[dict[str, Any]]:
    """Build finite row-metric residuals for positive candidates only."""

    output: list[dict[str, Any]] = []
    for row in rows:
        history_gap = _float(row.get("history_max_gap"))
        control_gap = _float(row.get("control_max_gap"))
        response_action_gap = _float(row.get("donor_response_action_only_gap"))
        hidden_specific_gap = _float(row.get("hidden_specific_gap"))
        role_weight = _float(row.get("role_weight", 0.0))
        non_history_gap = max(control_gap, response_action_gap)
        separation_margin = history_gap - non_history_gap
        residual = _softplus(non_history_gap - history_gap + float(margin))
        finite_values = [
            history_gap,
            control_gap,
            response_action_gap,
            hidden_specific_gap,
            role_weight,
            non_history_gap,
            separation_margin,
            residual,
        ]
        output.append(
            {
                "pair_id": str(row.get("pair_id", "")),
                "source_edge": str(row.get("source_edge", "")),
                "corpus_role": str(row.get("corpus_role", "")),
                "label": str(row.get("label", "")),
                "m1602_label": str(row.get("m1602_label", "")),
                "role_weight": role_weight,
                "history_max_gap": history_gap,
                "control_max_gap": control_gap,
                "donor_response_action_only_gap": response_action_gap,
                "hidden_specific_gap": hidden_specific_gap,
                "non_history_gap_max": non_history_gap,
                "history_control_separation_margin": separation_margin,
                "candidate_objective_residual": residual,
                "finite": bool(_all_finite(finite_values)),
                "positive_objective_row": True,
            }
        )
    return output


def diagnostic_guardrail_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build diagnostic rows that can never count as positive objective rows."""

    output: list[dict[str, Any]] = []
    for row in rows:
        role_weight = _float(row.get("role_weight", 0.0))
        history_gap = _float(row.get("history_max_gap"))
        control_gap = _float(row.get("control_max_gap"))
        response_action_gap = _float(row.get("donor_response_action_only_gap"))
        hidden_specific_gap = _float(row.get("hidden_specific_gap"))
        finite_values = [role_weight, history_gap, control_gap, response_action_gap, hidden_specific_gap]
        output.append(
            {
                "pair_id": str(row.get("pair_id", "")),
                "source_edge": str(row.get("source_edge", "")),
                "rule_reason": str(row.get("rule_reason", "")),
                "corpus_role": str(row.get("corpus_role", "")),
                "label": str(row.get("label", "")),
                "m1602_label": str(row.get("m1602_label", "")),
                "role_weight": role_weight,
                "history_max_gap": history_gap,
                "control_max_gap": control_gap,
                "donor_response_action_only_gap": response_action_gap,
                "hidden_specific_gap": hidden_specific_gap,
                "diagnostic_positive_weight": 0.0,
                "used_as_positive": False,
                "finite": bool(_all_finite(finite_values)),
            }
        )
    return output


def role_integrity_summary(
    positive_rows: Sequence[Mapping[str, Any]],
    diagnostic_rows: Sequence[Mapping[str, Any]],
    positive_eval_rows: Sequence[Mapping[str, Any]],
    diagnostic_eval_rows: Sequence[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> list[dict[str, Any]]:
    positive_ids = {str(row.get("pair_id", "")) for row in positive_rows}
    diagnostic_ids = {str(row.get("pair_id", "")) for row in diagnostic_rows}
    diagnostic_used = bool(positive_ids & diagnostic_ids) or any(
        str(row.get("corpus_role", "")) == POSITIVE_ROLE for row in diagnostic_rows
    )
    return [
        {
            "role": POSITIVE_ROLE,
            "input_row_count": len(positive_rows),
            "objective_row_count": len(positive_eval_rows),
            "role_weight_sum": sum(_float(row.get("role_weight", 0.0)) for row in positive_eval_rows),
            "diagnostic_rows_used_as_positive": False,
            "metadata_complete": _metadata_complete(manifest),
        },
        {
            "role": DIAGNOSTIC_ROLE,
            "input_row_count": len(diagnostic_rows),
            "objective_row_count": len(diagnostic_eval_rows),
            "role_weight_sum": sum(_float(row.get("role_weight", 0.0)) for row in diagnostic_eval_rows),
            "diagnostic_positive_weight_sum": sum(_float(row.get("diagnostic_positive_weight", 0.0)) for row in diagnostic_eval_rows),
            "diagnostic_rows_used_as_positive": bool(diagnostic_used),
            "metadata_complete": _metadata_complete(manifest),
        },
    ]


def objective_summary_rows(
    positive_eval_rows: Sequence[Mapping[str, Any]],
    diagnostic_eval_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    residuals = [_float(row.get("candidate_objective_residual")) for row in positive_eval_rows]
    margins = [_float(row.get("history_control_separation_margin")) for row in positive_eval_rows]
    hidden_specific = [_float(row.get("hidden_specific_gap")) for row in positive_eval_rows]
    return [
        {"metric": "candidate_objective_residual_mean", "value": _mean(residuals)},
        {"metric": "history_control_separation_margin_mean", "value": _mean(margins)},
        {"metric": "hidden_specific_gap_mean", "value": _mean(hidden_specific)},
        {"metric": "positive_finite_fraction", "value": _mean([1.0 if row.get("finite") else 0.0 for row in positive_eval_rows])},
        {"metric": "diagnostic_finite_fraction", "value": _mean([1.0 if row.get("finite") else 0.0 for row in diagnostic_eval_rows])},
    ]


def run_contour_aware_candidate_objective_evaluator(
    *,
    candidate_run_dir: Path | str,
    checkpoint: Path | str,
    run_dir: Path | str,
) -> dict[str, Any]:
    """Run a no-update full-package evaluator."""

    package_dir = Path(candidate_run_dir)
    checkpoint_path = Path(checkpoint)
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checksum_before = _sha256(checkpoint_path)

    package_summary = read_json(package_dir / "summary.json")
    corpus_manifest = read_json(package_dir / "corpus_manifest.json")
    positive_rows = read_csv_rows(package_dir / "positive_candidate_rows.csv")
    diagnostics = read_csv_rows(package_dir / "diagnostic_guardrail_rows.csv")

    positive_eval_rows = positive_objective_rows(positive_rows)
    diagnostic_eval_rows = diagnostic_guardrail_rows(diagnostics)
    role_rows = role_integrity_summary(positive_rows, diagnostics, positive_eval_rows, diagnostic_eval_rows, corpus_manifest)
    objective_rows = objective_summary_rows(positive_eval_rows, diagnostic_eval_rows)
    source_rows = []
    total = len(positive_rows)
    for edge, count in sorted(_source_edge_counts(positive_rows).items()):
        source_rows.append({"source_edge": edge, "positive_candidate_count": count, "share": count / total if total else 0.0})

    checksum_after = _sha256(checkpoint_path)
    checkpoint_weights_mutated = checksum_before != checksum_after
    positive_ids = {str(row.get("pair_id", "")) for row in positive_rows}
    diagnostic_ids = {str(row.get("pair_id", "")) for row in diagnostics}
    diagnostic_rows_used_as_positive = bool(positive_ids & diagnostic_ids) or any(
        str(row.get("corpus_role", "")) == POSITIVE_ROLE for row in diagnostics
    )
    diagnostic_positive_weight_sum = sum(_float(row.get("diagnostic_positive_weight", 0.0)) for row in diagnostic_eval_rows)
    positive_rows_all_clean = all(
        str(row.get("label", "")) == CLEAN_LABEL and str(row.get("m1602_label", "")) == CLEAN_LABEL
        for row in positive_rows
    )
    role_metadata_verified = (
        set(corpus_manifest.get("roles", [])) == {POSITIVE_ROLE, DIAGNOSTIC_ROLE}
        and int(corpus_manifest.get("positive_candidate_count", -1)) == len(positive_rows)
        and int(corpus_manifest.get("diagnostic_guardrail_count", -1)) == len(diagnostics)
        and _metadata_complete(corpus_manifest)
    )
    all_objective_metrics_finite = (
        all(bool(row["finite"]) for row in positive_eval_rows)
        and all(bool(row["finite"]) for row in diagnostic_eval_rows)
        and all(math.isfinite(_float(row["value"])) for row in objective_rows)
    )
    guardrail_violation_count = sum(1 for value in FORBIDDEN_GUARDRAILS.values() if bool(value))
    summary = {
        "result_class": "contour_aware_candidate_objective_evaluator_pass",
        "exact_evaluator_implemented": True,
        "candidate_objective_evaluated": True,
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256_before": checksum_before,
        "checkpoint_sha256_after": checksum_after,
        "checkpoint_weights_mutated": bool(checkpoint_weights_mutated),
        "candidate_run_dir": str(package_dir),
        "positive_candidate_count": len(positive_rows),
        "diagnostic_guardrail_count": len(diagnostics),
        "diagnostic_rows_used_as_positive": bool(diagnostic_rows_used_as_positive),
        "diagnostic_positive_weight_sum": float(diagnostic_positive_weight_sum),
        "positive_rows_all_clean": bool(positive_rows_all_clean),
        "role_metadata_verified": bool(role_metadata_verified),
        "public_proof_metadata_complete": bool(_metadata_complete(corpus_manifest)),
        "all_objective_metrics_finite": bool(all_objective_metrics_finite),
        "candidate_objective_residual_mean": _float(objective_rows[0]["value"]) if objective_rows else float("nan"),
        "history_control_separation_margin_mean": _float(objective_rows[1]["value"]) if len(objective_rows) > 1 else float("nan"),
        "hidden_specific_gap_mean": _float(objective_rows[2]["value"]) if len(objective_rows) > 2 else float("nan"),
        "source_edge_count": len(_source_edge_counts(positive_rows)),
        "max_source_edge_share": _max_share(_source_edge_counts(positive_rows)),
        "package_result_class": str(package_summary.get("result_class", "")),
        "guardrail_violation_count": int(guardrail_violation_count),
        **FORBIDDEN_GUARDRAILS,
    }
    summary["passes_public_smoke_gates"] = (
        bool(summary["exact_evaluator_implemented"])
        and bool(summary["candidate_objective_evaluated"])
        and int(summary["positive_candidate_count"]) == 39
        and int(summary["diagnostic_guardrail_count"]) == 232
        and not bool(summary["diagnostic_rows_used_as_positive"])
        and float(summary["diagnostic_positive_weight_sum"]) == 0.0
        and bool(summary["positive_rows_all_clean"])
        and bool(summary["role_metadata_verified"])
        and bool(summary["public_proof_metadata_complete"])
        and bool(summary["all_objective_metrics_finite"])
        and not bool(summary["checkpoint_weights_mutated"])
        and int(summary["guardrail_violation_count"]) == 0
        and not bool(summary["training_started"])
        and not bool(summary["ppo_used"])
        and not bool(summary["promoted"])
        and not bool(summary["private_holdout_used"])
        and not bool(summary["actor_input_contract_changed"])
        and not bool(summary["labels_enter_actor_input"])
        and not bool(summary["level3_self_id_claim_made"])
        and not bool(summary["training_corpus_exported"])
        and not bool(summary["loss_constructed"])
        and not bool(summary["objective_constructed"])
    )
    if bool(summary["diagnostic_rows_used_as_positive"]):
        null_class = "diagnostic_positive_leakage"
    elif not bool(summary["all_objective_metrics_finite"]):
        null_class = "nonfinite_objective_metrics"
    elif bool(summary["checkpoint_weights_mutated"]):
        null_class = "checkpoint_mutation_violation"
    elif not bool(summary["role_metadata_verified"]):
        null_class = "role_metadata_failure"
    elif bool(summary["passes_public_smoke_gates"]):
        null_class = "contour_aware_candidate_objective_evaluator_public_pass"
    else:
        null_class = "public_gate_failure"
    summary["null_result_classification"] = null_class
    summary["result_class"] = null_class

    guardrail_rows = [{"guardrail": "exact_evaluator_implemented", "violated": False, "value": True}]
    guardrail_rows.append({"guardrail": "checkpoint_weights_mutated", "violated": checkpoint_weights_mutated, "value": checkpoint_weights_mutated})
    guardrail_rows.extend({"guardrail": key, "violated": value, "value": value} for key, value in FORBIDDEN_GUARDRAILS.items())

    write_csv_rows(output / "positive_objective_rows.csv", positive_eval_rows)
    write_csv_rows(output / "diagnostic_guardrail_objective_rows.csv", diagnostic_eval_rows)
    write_csv_rows(output / "role_integrity_summary.csv", role_rows)
    write_csv_rows(output / "objective_summary.csv", objective_rows)
    write_csv_rows(output / "source_edge_summary.csv", source_rows)
    write_csv_rows(output / "guardrail_summary.csv", guardrail_rows)
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run no-update contour-aware candidate objective evaluator.")
    parser.add_argument("--candidate-run-dir", type=Path, default=DEFAULT_CANDIDATE_RUN_DIR)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    args = parser.parse_args()
    summary = run_contour_aware_candidate_objective_evaluator(
        candidate_run_dir=args.candidate_run_dir,
        checkpoint=args.checkpoint,
        run_dir=args.run_dir,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"positive_candidate_count={summary['positive_candidate_count']}")
    print(f"diagnostic_guardrail_count={summary['diagnostic_guardrail_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
