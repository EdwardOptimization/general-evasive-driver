"""No-training row15 unsafe-margin projection probe."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import (
    run_boundary_outcome_replay_gate,
    replay_boundary_rows_for_policy,
)
from autodrift.capability_step_temporal_sequence_update_probe import changed_parameter_names
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.outcome_intervention_eval import evaluate_checkpoint
from autodrift.outcome_intervention_optimize import save_checkpoint_like
from autodrift.trajectory_action_anchor_audit import audit_trajectory_action_anchor
from autodrift.train_ppo import resolve_device


DEFAULT_ALPHAS = (0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0)
ALLOWED_CHANGED_PREFIXES = ("actor_mean.", "response_context_fusion.0.")
ROW15_SURFACES: tuple[tuple[str, Path], ...] = (
    ("m223_m219", Path("runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv")),
    ("m267_m264", Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")),
    ("current_m333_surface", Path("runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("m314_continuity_surface", Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("m317_continuity_surface", Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
)
FIRST_REPLAY_SURFACES: tuple[tuple[str, str, Path], ...] = (
    ("old_public", "m183_m168", Path("runs/m183_m168_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("old_public", "m223_m219", Path("runs/m223_m219_boundary_outcome_corpus_seed10060/boundary_outcome_corpus.csv")),
    ("old_public", "m267_m264", Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")),
    ("source_diverse", "current_m333_surface", Path("runs/m320_m316_repaired_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("source_diverse", "m314_continuity_surface", Path("runs/m320_m314_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
    ("source_diverse", "m317_continuity_surface", Path("runs/m320_m316_boundary_outcome_corpus_seed10080/boundary_outcome_corpus.csv")),
)


def parse_alphas(text: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one alpha")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be in [0, 1]")
    return tuple(dict.fromkeys(values))


def alpha_label(alpha: float) -> str:
    return "alpha_" + f"{float(alpha):g}".replace(".", "_")


def _clone_state(model: torch.nn.Module) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def interpolate_state(
    base_state: dict[str, torch.Tensor],
    target_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    if set(base_state) != set(target_state):
        missing = sorted(set(base_state) - set(target_state))
        extra = sorted(set(target_state) - set(base_state))
        raise ValueError(f"state keys differ: missing={missing} extra={extra}")
    if float(alpha) < 0.0 or float(alpha) > 1.0:
        raise ValueError("alpha must be in [0, 1]")
    state: dict[str, torch.Tensor] = {}
    for name, base_tensor in base_state.items():
        target_tensor = target_state[name]
        if base_tensor.shape != target_tensor.shape:
            raise ValueError(f"state shape mismatch for {name}: {base_tensor.shape} vs {target_tensor.shape}")
        if torch.is_floating_point(base_tensor):
            state[name] = base_tensor + float(alpha) * (target_tensor - base_tensor)
        else:
            state[name] = base_tensor.clone()
    return state


def _config_signature(model: torch.nn.Module, checkpoint: dict[str, Any]) -> dict[str, Any]:
    config = checkpoint.get("config", {})
    return {
        "obs_dim": int(getattr(model, "obs_dim")),
        "act_dim": int(getattr(model, "act_dim")),
        "actor_encoder": str(getattr(model, "actor_encoder", "")),
        "actor_history_length": int(getattr(model, "actor_history_length", 1)),
        "action_sequence_horizon": int(getattr(model, "action_sequence_horizon", 1)),
        "config_actor_encoder": str(config.get("actor_encoder", "")),
    }


def actor_inputs_changed(base_checkpoint: Path, candidate_checkpoint: Path) -> bool:
    base_model, base_data = load_actor_critic_checkpoint(base_checkpoint, device="cpu")
    candidate_model, candidate_data = load_actor_critic_checkpoint(candidate_checkpoint, device="cpu")
    return _config_signature(base_model, base_data) != _config_signature(candidate_model, candidate_data)


def _allowed_parameter_change(changed: list[str]) -> bool:
    return all(any(name.startswith(prefix) for prefix in ALLOWED_CHANGED_PREFIXES) for name in changed)


def _write_row15_corpus(source_csv: Path, run_dir: Path, surface_label: str) -> Path:
    frame = pd.read_csv(source_csv)
    mask = frame["row_id"].astype(int).eq(15) & frame["physical_pair_key"].astype(str).eq("9530:21:9550:21")
    row15 = frame[mask].copy()
    if row15.empty:
        raise ValueError(f"surface {surface_label} has no row15 physical pair 9530:21:9550:21")
    if len(row15) != 1:
        raise ValueError(f"surface {surface_label} expected one row15 row, got {len(row15)}")
    path = run_dir / "row15_corpora" / f"{surface_label}_row15.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    row15.to_csv(path, index=False)
    return path


def _safe_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")
    return result


def _row15_gate_rows(
    *,
    checkpoint_specs: tuple[CheckpointSpec, ...],
    env_config: Path,
    max_continuation_steps: int,
    device: str,
    run_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    replay_rows: list[dict[str, Any]] = []
    gate_rows: list[dict[str, Any]] = []
    for surface_label, source_csv in ROW15_SURFACES:
        row15_csv = _write_row15_corpus(source_csv, run_dir, surface_label)
        corpus = pd.read_csv(row15_csv)
        surface_rows: list[dict[str, Any]] = []
        for spec in checkpoint_specs:
            rows = replay_boundary_rows_for_policy(
                checkpoint_spec=spec,
                corpus_frame=corpus,
                env_config_path=env_config,
                max_continuation_steps=max_continuation_steps,
                device=device,
            )
            for row in rows:
                row["surface_label"] = surface_label
            surface_rows.extend(rows)
            replay_rows.extend(rows)
        frame = pd.DataFrame(surface_rows)
        base_rows = frame[frame["policy"].astype(str).eq(alpha_label(0.0))]
        if len(base_rows) != 1:
            raise ValueError(f"expected one base row15 replay for {surface_label}, got {len(base_rows)}")
        base_wrong_margin = _safe_float(base_rows.iloc[0]["wrong_history_margin"])
        threshold = min(-0.00025, 0.5 * base_wrong_margin)
        for _, row in frame.iterrows():
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
                and wrong_margin <= threshold
            )
            gate_rows.append(
                {
                    "surface_label": surface_label,
                    "policy": row["policy"],
                    "checkpoint": row["checkpoint"],
                    "alpha": alpha,
                    "base_wrong_history_margin": base_wrong_margin,
                    "unsafe_margin_threshold": threshold,
                    "normal_success": normal_success,
                    "normal_margin": normal_margin,
                    "wrong_history_success": wrong_success,
                    "wrong_history_margin": wrong_margin,
                    "row15_unsafe_margin_pass": pass_row,
                }
            )
    return replay_rows, gate_rows


def _alpha_row15_pass(gate_rows: list[dict[str, Any]]) -> dict[float, bool]:
    frame = pd.DataFrame(gate_rows)
    result: dict[float, bool] = {}
    for alpha, group in frame.groupby("alpha", observed=True):
        alpha_value = float(alpha)
        result[alpha_value] = bool(alpha_value > 0.0 and len(group) == len(ROW15_SURFACES) and group["row15_unsafe_margin_pass"].all())
    return result


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
    for surface_tier, surface_label, corpus_csv in FIRST_REPLAY_SURFACES:
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
    target_anchor_npz: Path,
    combined_anchor_npz: Path,
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
                "run_type": "row15_unsafe_margin_projection_probe",
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
                "exact_m1107_loss": float(exact["loss_mean"]),
            }
        )
    if base_loss is None:
        raise RuntimeError("alpha 0.0 is required for baseline exact loss")
    for row in exact_rows:
        row["exact_m1107_delta_vs_base"] = float(row["exact_m1107_loss"]) - float(base_loss)
        row["exact_m1107_no_regression"] = bool(float(row["exact_m1107_delta_vs_base"]) <= 0.0)
        row["exact_m1107_improvement"] = bool(float(row["exact_m1107_delta_vs_base"]) < 0.0)

    target_anchor = audit_trajectory_action_anchor(
        checkpoints=tuple(checkpoint_specs),
        anchor_npz=target_anchor_npz,
        device=device,
        run_dir=run_dir / "target_base_anchor_audit",
    )
    combined_anchor = audit_trajectory_action_anchor(
        checkpoints=tuple(checkpoint_specs),
        anchor_npz=combined_anchor_npz,
        device=device,
        run_dir=run_dir / "combined_anchor_audit",
    )
    target_anchor_by_policy = {str(row["checkpoint_label"]): float(row["mse"]) for row in target_anchor["rows"]}
    combined_anchor_by_policy = {str(row["checkpoint_label"]): float(row["mse"]) for row in combined_anchor["rows"]}

    row15_replay_rows, row15_gate_rows = _row15_gate_rows(
        checkpoint_specs=tuple(checkpoint_specs),
        env_config=env_config,
        max_continuation_steps=max_continuation_steps,
        device=device,
        run_dir=run_dir,
    )
    row15_pass_by_alpha = _alpha_row15_pass(row15_gate_rows)

    exact_by_policy = {str(row["policy"]): row for row in exact_rows}
    candidate_summary_rows: list[dict[str, Any]] = []
    for row in candidate_rows:
        policy = str(row["policy"])
        alpha = float(row["alpha"])
        exact = exact_by_policy[policy]
        target_mse = target_anchor_by_policy[policy]
        combined_mse = combined_anchor_by_policy[policy]
        contract_pass = bool(row["allowed_parameter_change"]) and not bool(row["actor_inputs_changed"])
        exact_pass = bool(alpha > 0.0 and exact["exact_m1107_no_regression"] and exact["exact_m1107_improvement"])
        anchor_pass = bool(target_mse <= 0.0001 and combined_mse <= 0.0001)
        row15_pass = bool(row15_pass_by_alpha.get(alpha, False))
        candidate_summary_rows.append(
            {
                **row,
                **exact,
                "target_base_trajectory_mse": target_mse,
                "combined_trajectory_mse": combined_mse,
                "contract_pass": contract_pass,
                "exact_pass": exact_pass,
                "anchor_pass": anchor_pass,
                "row15_unsafe_margin_pass": row15_pass,
                "projection_candidate_pass": bool(contract_pass and exact_pass and anchor_pass and row15_pass),
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

    if selected is None:
        result_class = "row15_unsafe_margin_projection_no_candidate"
        next_route = "objective_redesign_or_terminal_margin_target_export"
        failure_types = ["proof_washout"]
    elif not first_replay_pass:
        result_class = "row15_unsafe_margin_projection_first_replay_failed"
        next_route = "row15_unsafe_margin_projection_first_replay_failure_audit"
        failure_types = ["proof_washout"]
    else:
        result_class = "row15_unsafe_margin_projection_first_replay_candidate"
        next_route = "family_intersection_replay_design_only"
        failure_types = ["none"]

    write_csv_rows(run_dir / "projection_candidates.csv", candidate_summary_rows)
    write_csv_rows(run_dir / "row15_replay_rows.csv", row15_replay_rows)
    write_csv_rows(run_dir / "row15_gate_rows.csv", row15_gate_rows)
    write_csv_rows(run_dir / "first_replay_summary.csv", first_replay_rows)
    summary = {
        "run_type": "row15_unsafe_margin_projection_probe",
        "result_class": result_class,
        "failure_types": failure_types,
        "base_checkpoint": str(base_checkpoint),
        "target_checkpoint": str(target_checkpoint),
        "snippet_npz": str(snippet_npz),
        "target_anchor_npz": str(target_anchor_npz),
        "combined_anchor_npz": str(combined_anchor_npz),
        "alphas": list(alphas),
        "candidate_count": len(candidate_summary_rows),
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
        "row15_replay_rows_csv": str(run_dir / "row15_replay_rows.csv"),
        "row15_gate_rows_csv": str(run_dir / "row15_gate_rows.csv"),
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
    parser.add_argument("--target-anchor-npz", type=Path, required=True)
    parser.add_argument("--combined-anchor-npz", type=Path, required=True)
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
        target_anchor_npz=args.target_anchor_npz,
        combined_anchor_npz=args.combined_anchor_npz,
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
