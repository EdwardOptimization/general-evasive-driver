"""Materialize one fusion_actor repaired checkpoint artifact."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.clean_active_set_contour_mapper import read_csv_rows
from autodrift.contour_aware_policy_target_exact_evaluator import DEFAULT_MATERIALIZATION_RUN_DIR
from autodrift.contour_aware_tensor_capture_dry_run import _sha256
from autodrift.decisive_history_bounded_runner import DEFAULT_CHECKPOINT
from autodrift.fusion_actor_proposal_repair import (
    FUSION_ACTOR_SCOPE,
    MIN_CANDIDATE_REDUCTION_RATIO,
    PRIMARY_ALPHA,
    run_fusion_actor_candidate_repair,
)
from autodrift.selected_proposal_repair import DEFAULT_CANDIDATE_SUMMARY, _bool, _safe_id
from autodrift.selected_proposal_scope_sensitivity import FEATURE_MODE_DIFFERENTIABLE


DEFAULT_RUN_DIR = Path("runs/m1663_fusion_actor_checkpoint_artifact")
DEFAULT_PROPOSAL_CHECKPOINT = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_2.pt")
ARTIFACT_FILENAME = "alpha_0_2_fusion_actor_repaired.pt"
ARTIFACT_LABEL = "objective_sanity_artifact_only"

ArtifactRepairFunction = Callable[..., dict[str, Any]]


def _float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _select_candidate_row(rows: Sequence[Mapping[str, Any]], selected_alpha: float) -> dict[str, Any]:
    matches = [dict(row) for row in rows if abs(_float(row.get("alpha")) - float(selected_alpha)) <= 1e-12]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one candidate row for alpha {selected_alpha}, found {len(matches)}")
    return matches[0]


def _write_checksums(path: Path, entries: Mapping[str, Path]) -> dict[str, str]:
    checksums: dict[str, str] = {}
    lines: list[str] = []
    for label, entry in entries.items():
        checksum = _sha256(entry) if entry.exists() else ""
        checksums[label] = checksum
        lines.append(f"{checksum}  {label}  {entry}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return checksums


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "checkpoint_artifact_count",
        "unexpected_checkpoint_artifact_count",
        "excluded_parameter_delta_violation_count",
        "diagnostic_rows_used_as_positive_count",
        "donor_plus_action_used_as_loss_target_count",
        "training_started_count",
        "ppo_used_count",
        "promoted_count",
        "private_holdout_used_count",
        "actor_input_contract_changed_count",
        "level3_self_id_claim_count",
    ]
    return [{"guardrail": key, "violated": bool(summary.get(key, 0)) if key != "checkpoint_artifact_count" else int(summary.get(key, 0)) != 1, "value": summary.get(key)} for key in keys]


def _candidate_output_row(candidate: Mapping[str, Any], artifact_path: Path) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "alpha": candidate.get("alpha"),
        "artifact_path": str(artifact_path),
        "initial_positive_exact_residual_mean": candidate.get("initial_positive_exact_residual_mean"),
        "repaired_positive_exact_residual_mean": candidate.get("repaired_positive_exact_residual_mean"),
        "positive_exact_residual_reduction_ratio": candidate.get("positive_exact_residual_reduction_ratio"),
        "accepted_backtracking_step_count": candidate.get("accepted_backtracking_step_count"),
        "excluded_parameter_delta_max": candidate.get("excluded_parameter_delta_max"),
        "passes_candidate_gate": candidate.get("passes_candidate_gate"),
        "null_result_classification": candidate.get("null_result_classification"),
        "guardrail_violation_count": candidate.get("guardrail_violation_count"),
    }


def run_fusion_actor_checkpoint_artifact(
    *,
    base_checkpoint: Path | str,
    proposal_checkpoint: Path | str,
    candidate_summary: Path | str,
    materialization_run_dir: Path | str,
    run_dir: Path | str,
    selected_alpha: float = PRIMARY_ALPHA,
    device: str = "cpu",
    repair_fn: ArtifactRepairFunction = run_fusion_actor_candidate_repair,
) -> dict[str, Any]:
    """Materialize the primary alpha 0.2 repaired checkpoint artifact."""

    if abs(float(selected_alpha) - PRIMARY_ALPHA) > 1e-12:
        raise ValueError("M1663 only admits the alpha 0.2 primary artifact")
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = output / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = checkpoint_dir / ARTIFACT_FILENAME
    rows = read_csv_rows(candidate_summary)
    source_row = _select_candidate_row(rows, selected_alpha)
    candidate_id = str(source_row.get("candidate_id", "alpha_0_2"))
    candidate_run_dir = output / "candidates" / _safe_id(candidate_id)
    base_path = Path(base_checkpoint)
    proposal_path = Path(proposal_checkpoint)
    m1660_summary = Path("runs/m1660_fusion_actor_proposal_repair/summary.json")
    m1660_guardrails = Path("runs/m1660_fusion_actor_proposal_repair/guardrail_summary.csv")
    candidate = repair_fn(
        materialization_run_dir=materialization_run_dir,
        base_checkpoint=base_path,
        proposal_checkpoint=proposal_path,
        candidate_id=candidate_id,
        alpha=float(selected_alpha),
        run_dir=candidate_run_dir,
        device=device,
        checkpoint_artifact_path=artifact_path,
        checkpoint_artifacts_allowed=True,
        checkpoint_metadata={
            "artifact_label": ARTIFACT_LABEL,
            "artifact_id": "m1663_alpha_0_2_fusion_actor_repaired",
            "source_milestone": "m1660-paper-route-fusion-actor-proposal-repair-implementation",
            "materialization_milestone": "m1663-paper-route-fusion-actor-checkpoint-artifact-implementation",
        },
    )
    checkpoint_artifacts = sorted(output.rglob("*.pt")) + sorted(output.rglob("*.pth"))
    checkpoint_artifact_count = len(checkpoint_artifacts)
    unexpected_checkpoint_artifact_count = max(0, checkpoint_artifact_count - 1)
    artifact_exists = artifact_path.exists()
    checksums = _write_checksums(
        output / "checksums.sha256",
        {
            "base_checkpoint": base_path,
            "proposal_checkpoint": proposal_path,
            "artifact_checkpoint": artifact_path,
            "source_candidate_summary": Path(candidate_summary),
            "source_m1660_summary": m1660_summary,
            "source_m1660_guardrail_summary": m1660_guardrails,
        },
    )
    reduction_ratio = _float(candidate.get("positive_exact_residual_reduction_ratio"))
    excluded_delta_max = _float(candidate.get("excluded_parameter_delta_max"))
    candidate_public_pass = _bool(candidate.get("passes_candidate_gate"))
    guardrail_violation_count = int(candidate.get("guardrail_violation_count", 0) or 0)
    excluded_parameter_delta_violation_count = 1 if excluded_delta_max != 0.0 else 0
    summary: dict[str, Any] = {
        "result_class": "",
        "artifact_label": ARTIFACT_LABEL,
        "artifact_id": "m1663_alpha_0_2_fusion_actor_repaired",
        "artifact_path": str(artifact_path),
        "artifact_sha256": checksums.get("artifact_checkpoint", ""),
        "git_commit": _git_commit(),
        "base_checkpoint": str(base_path),
        "base_checkpoint_sha256": checksums.get("base_checkpoint", ""),
        "proposal_checkpoint": str(proposal_path),
        "proposal_checkpoint_sha256": checksums.get("proposal_checkpoint", ""),
        "source_candidate_summary": str(candidate_summary),
        "source_m1660_summary": str(m1660_summary),
        "source_m1660_guardrail_summary": str(m1660_guardrails),
        "selected_alpha": float(selected_alpha),
        "selected_candidate_id": candidate_id,
        "feature_mode": FEATURE_MODE_DIFFERENTIABLE,
        "trainable_scope": FUSION_ACTOR_SCOPE,
        "checkpoint_artifact_count": int(checkpoint_artifact_count),
        "unexpected_checkpoint_artifact_count": int(unexpected_checkpoint_artifact_count),
        "artifact_exists": bool(artifact_exists),
        "candidate_public_pass": bool(candidate_public_pass),
        "initial_positive_exact_residual_mean": candidate.get("initial_positive_exact_residual_mean"),
        "repaired_positive_exact_residual_mean": candidate.get("repaired_positive_exact_residual_mean"),
        "positive_exact_residual_reduction_ratio": reduction_ratio,
        "accepted_backtracking_step_count": int(candidate.get("accepted_backtracking_step_count", 0) or 0),
        "excluded_parameter_delta_max": excluded_delta_max,
        "excluded_parameter_delta_violation_count": int(excluded_parameter_delta_violation_count),
        "candidate_guardrail_violation_count": int(guardrail_violation_count),
        "diagnostic_rows_used_as_positive_count": 0,
        "donor_plus_action_used_as_loss_target_count": 0,
        "training_started_count": 0,
        "ppo_used_count": 0,
        "promoted_count": 0,
        "private_holdout_used_count": 0,
        "actor_input_contract_changed_count": 0,
        "level3_self_id_claim_count": 0,
    }
    passes = (
        bool(artifact_exists)
        and checkpoint_artifact_count == 1
        and unexpected_checkpoint_artifact_count == 0
        and abs(float(selected_alpha) - PRIMARY_ALPHA) <= 1e-12
        and candidate_public_pass
        and reduction_ratio >= MIN_CANDIDATE_REDUCTION_RATIO
        and excluded_parameter_delta_violation_count == 0
        and guardrail_violation_count == 0
        and int(summary["diagnostic_rows_used_as_positive_count"]) == 0
        and int(summary["donor_plus_action_used_as_loss_target_count"]) == 0
        and int(summary["training_started_count"]) == 0
        and int(summary["ppo_used_count"]) == 0
        and int(summary["promoted_count"]) == 0
        and int(summary["private_holdout_used_count"]) == 0
        and int(summary["actor_input_contract_changed_count"]) == 0
        and int(summary["level3_self_id_claim_count"]) == 0
    )
    if not artifact_exists:
        result_class = "checkpoint_artifact_missing"
    elif checkpoint_artifact_count != 1:
        result_class = "checkpoint_artifact_count_mismatch"
    elif not candidate_public_pass:
        result_class = "candidate_public_gate_failure"
    elif reduction_ratio < MIN_CANDIDATE_REDUCTION_RATIO:
        result_class = "objective_reduction_below_threshold"
    elif excluded_parameter_delta_violation_count != 0:
        result_class = "excluded_parameter_delta_violation"
    elif guardrail_violation_count != 0:
        result_class = "candidate_guardrail_violation"
    elif passes:
        result_class = "fusion_actor_checkpoint_artifact_public_pass"
    else:
        result_class = "public_gate_failure"
    summary["passes_public_smoke_gates"] = bool(passes)
    summary["null_result_classification"] = result_class
    summary["result_class"] = result_class
    metadata = {
        key: summary[key]
        for key in (
            "artifact_label",
            "artifact_id",
            "artifact_path",
            "artifact_sha256",
            "git_commit",
            "base_checkpoint",
            "base_checkpoint_sha256",
            "proposal_checkpoint",
            "proposal_checkpoint_sha256",
            "source_candidate_summary",
            "source_m1660_summary",
            "source_m1660_guardrail_summary",
            "selected_alpha",
            "selected_candidate_id",
            "feature_mode",
            "trainable_scope",
            "initial_positive_exact_residual_mean",
            "repaired_positive_exact_residual_mean",
            "positive_exact_residual_reduction_ratio",
            "accepted_backtracking_step_count",
            "excluded_parameter_delta_max",
            "checkpoint_artifact_count",
            "private_holdout_used_count",
            "promoted_count",
        )
    }
    write_json(output / "artifact_metadata.json", metadata)
    write_csv_rows(output / "candidate_summary.csv", [_candidate_output_row(candidate, artifact_path)])
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize one fusion_actor repaired checkpoint artifact.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--proposal-checkpoint", type=Path, default=DEFAULT_PROPOSAL_CHECKPOINT)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--materialization-run-dir", type=Path, default=DEFAULT_MATERIALIZATION_RUN_DIR)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--selected-alpha", type=float, default=PRIMARY_ALPHA)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    args = parser.parse_args()
    summary = run_fusion_actor_checkpoint_artifact(
        base_checkpoint=args.base_checkpoint,
        proposal_checkpoint=args.proposal_checkpoint,
        candidate_summary=args.candidate_summary,
        materialization_run_dir=args.materialization_run_dir,
        run_dir=args.run_dir,
        selected_alpha=args.selected_alpha,
        device=args.device,
    )
    print(f"summary={args.run_dir / 'summary.json'}")
    print(f"artifact={summary['artifact_path']}")
    print(f"checkpoint_artifact_count={summary['checkpoint_artifact_count']}")
    print(f"passes_public_smoke_gates={summary['passes_public_smoke_gates']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
