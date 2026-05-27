"""No-training unsafe-margin projection probe for promoted row15 surfaces."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import (
    run_boundary_outcome_replay_gate,
    replay_boundary_rows_for_policy,
    validate_corpus_frame,
)
from autodrift.capability_step_temporal_sequence_update_probe import changed_parameter_names
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.outcome_intervention_eval import evaluate_checkpoint
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.row15_unsafe_margin_projection_probe import (
    _allowed_parameter_change,
    actor_inputs_changed,
    alpha_label,
    interpolate_state,
    parse_alphas,
)
from autodrift.train_ppo import resolve_device


DEFAULT_ALPHAS = (
    0.0,
    0.005,
    0.01,
    0.02,
    0.03,
    0.04,
    0.05,
    0.075,
    0.1,
    0.125,
    0.15,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.75,
    1.0,
)

DEFAULT_FIRST_REPLAY_SURFACES: tuple[tuple[str, str, Path], ...] = (
    ("old_public", "m183_m168", Path("runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("old_public", "m183_m170", Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("old_public", "m193_m189", Path("runs/m193_m189_boundary_outcome_corpus_seed9630/boundary_outcome_corpus.csv")),
    ("old_public", "m212_m204", Path("runs/m212_m204_boundary_outcome_corpus_seed10040/boundary_outcome_corpus.csv")),
    ("old_public", "m223_m219", Path("runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv")),
    ("old_public", "m267_m264", Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")),
    (
        "source_diverse",
        "current_m333_surface",
        Path("runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv"),
    ),
    ("source_diverse", "m314_continuity_surface", Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("source_diverse", "m317_continuity_surface", Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    (
        "row15_promoted",
        "row15_promoted_materialized",
        Path("runs/m1149_row15_promoted_actor_update_first_replay/row15_promoted_materialized_corpus.csv"),
    ),
)

REQUIRED_FAILED_ROW_COLUMNS = (
    "surface",
    "row_id",
    "target",
    "physical_pair_key",
    "left_seed",
    "right_seed",
    "left_step",
    "right_step",
    "relocated_obstacle_body_x",
    "relocated_obstacle_body_y",
    "relocated_obstacle_half_width",
)


def _clone_state(model: Any) -> dict[str, Any]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def validate_failed_rows_frame(frame: pd.DataFrame) -> None:
    missing = [column for column in REQUIRED_FAILED_ROW_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError("failed rows CSV is missing columns: " + ", ".join(missing))
    validate_corpus_frame(frame)


def group_failed_rows_by_surface(frame: pd.DataFrame) -> dict[str, pd.DataFrame]:
    validate_failed_rows_frame(frame)
    groups: dict[str, pd.DataFrame] = {}
    for surface, group in frame.groupby("surface", sort=True, dropna=False):
        label = str(surface)
        if not label:
            raise ValueError("failed rows CSV contains an empty surface label")
        groups[label] = group.reset_index(drop=True).copy()
    if not groups:
        raise ValueError("failed rows CSV contains no rows")
    return groups


def alpha_failed_rows_pass(gate_rows: list[dict[str, Any]], *, failed_row_count: int) -> dict[float, bool]:
    frame = pd.DataFrame(gate_rows)
    result: dict[float, bool] = {}
    if frame.empty:
        return result
    for alpha, group in frame.groupby("alpha", observed=True):
        alpha_value = float(alpha)
        result[alpha_value] = bool(
            alpha_value > 0.0
            and len(group) == int(failed_row_count)
            and group["failed_row_unsafe_margin_pass"].astype(bool).all()
        )
    return result


def classify_projection_result(*, selected: dict[str, Any] | None, first_replay_pass: bool) -> tuple[str, str, list[str]]:
    if selected is None:
        return (
            "row15_promoted_unsafe_margin_projection_no_candidate",
            "terminal_margin_objective_design",
            ["proof_washout"],
        )
    if not first_replay_pass:
        return (
            "row15_promoted_unsafe_margin_projection_first_replay_failed",
            "row15_promoted_unsafe_margin_projection_first_replay_failure_audit",
            ["proof_washout"],
        )
    return (
        "row15_promoted_unsafe_margin_projection_first_replay_candidate",
        "family_intersection_and_behavior_diagnostic_design_only",
        ["none"],
    )


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _write_failed_row_corpora(frame: pd.DataFrame, run_dir: Path) -> dict[str, Path]:
    paths: dict[str, Path] = {}
    for surface, group in group_failed_rows_by_surface(frame).items():
        path = run_dir / "failed_row_corpora" / f"{surface}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        group.to_csv(path, index=False)
        paths[surface] = path
    return paths


def _failed_row_gate_rows(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    failed_rows_csv: Path,
    env_config: Path,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    failed_frame = pd.read_csv(failed_rows_csv)
    validate_failed_rows_frame(failed_frame)
    failed_row_count = int(len(failed_frame))
    corpus_paths = _write_failed_row_corpora(failed_frame, run_dir)
    replay_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for surface, corpus_path in corpus_paths.items():
        corpus = pd.read_csv(corpus_path)
        for spec in checkpoint_specs:
            rows = replay_boundary_rows_for_policy(
                checkpoint_spec=spec,
                corpus_frame=corpus,
                env_config_path=env_config,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            for row in rows:
                row["surface_label"] = surface
                replay_rows.append(row)
                alpha = float(str(row["policy"]).replace("alpha_", "").replace("_", "."))
                normal_success = bool(row["normal_success"])
                wrong_success = bool(row["wrong_history_success"])
                normal_margin = _safe_float(row["normal_margin"])
                wrong_margin = _safe_float(row["wrong_history_margin"])
                pass_row = bool(
                    alpha > 0.0
                    and normal_success
                    and np.isfinite(normal_margin)
                    and normal_margin >= 0.0
                    and not wrong_success
                    and np.isfinite(wrong_margin)
                    and wrong_margin < 0.0
                )
                gate_rows.append(
                    {
                        "surface_label": surface,
                        "policy": row["policy"],
                        "checkpoint": row["checkpoint"],
                        "alpha": alpha,
                        "row_id": int(row["row_id"]),
                        "target": str(row["target"]),
                        "physical_pair_key": str(row["physical_pair_key"]),
                        "normal_success": normal_success,
                        "normal_margin": normal_margin,
                        "wrong_history_success": wrong_success,
                        "wrong_history_margin": wrong_margin,
                        "failed_row_unsafe_margin_pass": pass_row,
                    }
                )
    return replay_rows, gate_rows, failed_row_count


def _first_replay(
    *,
    base_checkpoint: Path,
    candidate_checkpoint: Path,
    candidate_label: str,
    env_config: Path,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    specs = (
        CheckpointSpec(label=alpha_label(0.0), path=base_checkpoint),
        CheckpointSpec(label=candidate_label, path=candidate_checkpoint),
    )
    for surface_tier, surface_label, corpus_csv in DEFAULT_FIRST_REPLAY_SURFACES:
        surface_dir = run_dir / "first_replay" / surface_label
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=specs,
            corpus_csv=corpus_csv,
            env_config_path=env_config,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=alpha_label(0.0),
            candidate_policy=candidate_label,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=surface_dir,
        )
        rows.append(
            {
                "surface_tier": surface_tier,
                "surface_label": surface_label,
                "rows": int(summary["rows"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "wrong_history_success_delta": float(summary["wrong_history_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "gate_pass": bool(summary["gate_pass"]),
                "run_dir": str(surface_dir),
            }
        )
    return rows, all(bool(row["gate_pass"]) for row in rows)


def run_projection_probe(
    *,
    base_checkpoint: Path,
    target_checkpoint: Path,
    snippet_npz: Path,
    failed_rows_csv: Path,
    env_config: Path,
    alphas: tuple[float, ...],
    max_continuation_steps: int,
    logprob_margin: float,
    device: str,
    run_dir: Path,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    base_model, base_data = load_actor_critic_checkpoint(base_checkpoint, device=str(resolved_device))
    target_model, _ = load_actor_critic_checkpoint(target_checkpoint, device=str(resolved_device))
    base_state = _clone_state(base_model)
    target_state = _clone_state(target_model)

    checkpoint_specs: list[CheckpointSpec] = []
    candidate_rows: list[dict[str, Any]] = []
    checkpoint_dir = run_dir / "checkpoints"
    for alpha in alphas:
        state = interpolate_state(base_state, target_state, alpha)
        base_model.load_state_dict({name: tensor.to(device=resolved_device) for name, tensor in state.items()})
        label = alpha_label(alpha)
        checkpoint_path = checkpoint_dir / f"{label}.pt"
        save_checkpoint_like(
            model=base_model,
            source_checkpoint=base_data,
            path=checkpoint_path,
            metadata={
                "run_type": "row15_promoted_unsafe_margin_projection_probe",
                "base_checkpoint": str(base_checkpoint),
                "target_checkpoint": str(target_checkpoint),
                "alpha": float(alpha),
                "training_started": False,
                "ppo_used": False,
                "promoted": False,
                "private_holdout_used": False,
            },
        )
        changed = changed_parameter_names(base_state, state)
        candidate_rows.append(
            {
                "policy": label,
                "alpha": float(alpha),
                "checkpoint": str(checkpoint_path),
                "changed_parameter_count": len(changed),
                "changed_parameter_names": ";".join(changed),
                "allowed_parameter_change": _allowed_parameter_change(changed),
                "actor_inputs_changed": actor_inputs_changed(base_checkpoint, checkpoint_path),
            }
        )
        checkpoint_specs.append(CheckpointSpec(label=label, path=checkpoint_path))

    exact_rows: list[dict[str, Any]] = []
    base_loss = None
    for spec in checkpoint_specs:
        exact, _ = evaluate_checkpoint(
            label=spec.label,
            checkpoint=spec.path,
            snippet_npz=snippet_npz,
            device=device,
            batch_size=1,
            batches=1,
            seed=0,
            logprob_margin=logprob_margin,
            exact=True,
        )
        if spec.label == alpha_label(0.0):
            base_loss = float(exact["loss_mean"])
        exact_rows.append(
            {
                "policy": spec.label,
                "checkpoint": str(spec.path),
                "exact_m1144_loss": float(exact["loss_mean"]),
            }
        )
    if base_loss is None:
        raise RuntimeError("alpha 0.0 is required for baseline exact loss")
    for row in exact_rows:
        row["exact_m1144_delta_vs_base"] = float(row["exact_m1144_loss"]) - float(base_loss)
        row["exact_m1144_no_regression"] = bool(float(row["exact_m1144_delta_vs_base"]) <= 0.0)
        row["exact_m1144_improvement"] = bool(float(row["exact_m1144_delta_vs_base"]) < 0.0)

    failed_replay_rows, failed_gate_rows, failed_row_count = _failed_row_gate_rows(
        checkpoint_specs=tuple(checkpoint_specs),
        failed_rows_csv=failed_rows_csv,
        env_config=env_config,
        max_continuation_steps=max_continuation_steps,
        device=device,
        run_dir=run_dir,
    )
    failed_pass_by_alpha = alpha_failed_rows_pass(failed_gate_rows, failed_row_count=failed_row_count)

    exact_by_policy = {str(row["policy"]): row for row in exact_rows}
    candidate_summary_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        policy = str(row["policy"])
        alpha = float(row["alpha"])
        exact = exact_by_policy[policy]
        contract_pass = bool(row["allowed_parameter_change"]) and not bool(row["actor_inputs_changed"])
        exact_pass = bool(alpha > 0.0 and exact["exact_m1144_no_regression"] and exact["exact_m1144_improvement"])
        failed_rows_pass = bool(failed_pass_by_alpha.get(alpha, False))
        candidate_summary_rows.append(
            {
                **row,
                **exact,
                "contract_pass": contract_pass,
                "exact_pass": exact_pass,
                "failed_row_unsafe_margin_pass": failed_rows_pass,
                "projection_candidate_pass": bool(contract_pass and exact_pass and failed_rows_pass),
            }
        )
    eligible = [row for row in candidate_summary_rows if bool(row["projection_candidate_pass"])]
    selected = sorted(eligible, key=lambda row: float(row["alpha"]), reverse=True)[0] if eligible else None

    first_replay_rows: list[dict[str, Any]] = []
    first_replay_pass = False
    if selected is not None:
        first_replay_rows, first_replay_pass = _first_replay(
            base_checkpoint=Path(str(candidate_summary_rows[0]["checkpoint"])),
            candidate_checkpoint=Path(str(selected["checkpoint"])),
            candidate_label=str(selected["policy"]),
            env_config=env_config,
            max_continuation_steps=max_continuation_steps,
            device=device,
            run_dir=run_dir,
        )

    result_class, next_route, failure_types = classify_projection_result(
        selected=selected,
        first_replay_pass=first_replay_pass,
    )

    write_csv_rows(run_dir / "projection_candidates.csv", candidate_summary_rows)
    write_csv_rows(run_dir / "failed_row_replay_rows.csv", failed_replay_rows)
    write_csv_rows(run_dir / "failed_row_gate_rows.csv", failed_gate_rows)
    write_csv_rows(run_dir / "first_replay_summary.csv", first_replay_rows)
    summary = {
        "run_type": "row15_promoted_unsafe_margin_projection_probe",
        "result_class": result_class,
        "failure_types": failure_types,
        "base_checkpoint": str(base_checkpoint),
        "target_checkpoint": str(target_checkpoint),
        "snippet_npz": str(snippet_npz),
        "failed_rows_csv": str(failed_rows_csv),
        "alphas": list(alphas),
        "candidate_count": len(candidate_summary_rows),
        "failed_row_count": int(failed_row_count),
        "projection_candidate_pass_count": len(eligible),
        "selected_alpha": None if selected is None else float(selected["alpha"]),
        "selected_policy": None if selected is None else str(selected["policy"]),
        "selected_checkpoint": None if selected is None else str(selected["checkpoint"]),
        "first_replay_pass": bool(first_replay_pass),
        "first_replay_surface_count": len(first_replay_rows),
        "next_route": next_route,
        "training_started": False,
        "actor_training_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "family_intersection_replay_started": False,
        "full_public_gate_started": False,
        "fresh_ood_started": False,
        "behavior_gate_started": False,
        "actor_inputs_changed": any(bool(row["actor_inputs_changed"]) for row in candidate_summary_rows),
        "projection_candidates_csv": str(run_dir / "projection_candidates.csv"),
        "failed_row_replay_rows_csv": str(run_dir / "failed_row_replay_rows.csv"),
        "failed_row_gate_rows_csv": str(run_dir / "failed_row_gate_rows.csv"),
        "first_replay_summary_csv": str(run_dir / "first_replay_summary.csv"),
        "summary_json": str(run_dir / "summary.json"),
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--target-checkpoint", type=Path, required=True)
    parser.add_argument("--snippet-npz", type=Path, required=True)
    parser.add_argument("--failed-rows-csv", type=Path, required=True)
    parser.add_argument("--env-config", type=Path, required=True)
    parser.add_argument("--alphas", type=parse_alphas, default=DEFAULT_ALPHAS)
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    parser.add_argument("--logprob-margin", type=float, default=0.05)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = run_projection_probe(
        base_checkpoint=args.base_checkpoint,
        target_checkpoint=args.target_checkpoint,
        snippet_npz=args.snippet_npz,
        failed_rows_csv=args.failed_rows_csv,
        env_config=args.env_config,
        alphas=args.alphas,
        max_continuation_steps=args.max_continuation_steps,
        logprob_margin=args.logprob_margin,
        device=args.device,
        run_dir=args.run_dir,
    )
    print(f"result_class={summary['result_class']}")
    print(f"selected_alpha={summary['selected_alpha']}")
    print(f"first_replay_pass={summary['first_replay_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
