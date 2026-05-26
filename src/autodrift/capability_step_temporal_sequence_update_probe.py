"""Actor-mean-only exact update probe for the temporal sequence objective."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json
from autodrift.capability_step_temporal_sequence_objective import (
    load_corpus,
    sequence_lengths,
    temporal_preference_loss,
    weighted_mean,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.matched_history_intervention_gate import deterministic_action_from_hidden
from autodrift.train_ppo import ActorCritic, resolve_device


DEFAULT_ALPHAS = (0.005, 0.010, 0.020, 0.050, 0.100, 0.200, 0.500, 1.000)
ACTOR_MEAN_PREFIX = "actor_mean."


def parse_alphas(text: str) -> tuple[float, ...]:
    values = tuple(float(item.strip()) for item in str(text).split(",") if item.strip())
    if not values:
        raise argparse.ArgumentTypeError("expected at least one alpha")
    if any(value < 0.0 for value in values):
        raise argparse.ArgumentTypeError("alphas must be non-negative")
    return values


def clone_state_dict(model: ActorCritic) -> dict[str, torch.Tensor]:
    return {name: tensor.detach().cpu().clone() for name, tensor in model.state_dict().items()}


def state_checksum(state: dict[str, torch.Tensor], *, exclude_actor_mean: bool = False) -> str:
    digest = hashlib.sha256()
    for name, tensor in sorted(state.items()):
        if exclude_actor_mean and name.startswith(ACTOR_MEAN_PREFIX):
            continue
        digest.update(name.encode("utf-8"))
        array = tensor.detach().cpu().contiguous().numpy()
        digest.update(str(array.dtype).encode("utf-8"))
        digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
        digest.update(array.tobytes())
    return digest.hexdigest()


def changed_parameter_names(
    base_state: dict[str, torch.Tensor],
    candidate_state: dict[str, torch.Tensor],
) -> list[str]:
    changed: list[str] = []
    for name, base_tensor in sorted(base_state.items()):
        candidate_tensor = candidate_state[name]
        if not torch.equal(base_tensor.cpu(), candidate_tensor.cpu()):
            changed.append(name)
    return changed


def set_actor_mean_trainable_only(model: ActorCritic) -> None:
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    for parameter in model.actor_mean.parameters():
        parameter.requires_grad_(True)


def interpolate_actor_mean_state(
    base_state: dict[str, torch.Tensor],
    raw_state: dict[str, torch.Tensor],
    alpha: float,
) -> dict[str, torch.Tensor]:
    output: dict[str, torch.Tensor] = {}
    alpha_value = float(alpha)
    for name, base_tensor in base_state.items():
        if name.startswith(ACTOR_MEAN_PREFIX):
            output[name] = base_tensor + alpha_value * (raw_state[name] - base_tensor)
        else:
            output[name] = base_tensor.clone()
    return output


def _save_checkpoint(
    *,
    checkpoint_data: dict[str, Any],
    state_dict: dict[str, torch.Tensor],
    destination: Path,
    objective: str,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    output = dict(checkpoint_data)
    output["model_state"] = {name: tensor.detach().cpu() for name, tensor in state_dict.items()}
    config = dict(output.get("config", {}))
    config["objective"] = objective
    output["config"] = config
    torch.save(output, destination)


def tensors_from_corpus(corpus: dict[str, np.ndarray], device: torch.device) -> dict[str, torch.Tensor]:
    return {
        "obs": torch.as_tensor(corpus["normal_rollout_observations"], dtype=torch.float32, device=device).transpose(0, 1),
        "actions": torch.as_tensor(corpus["normal_rollout_actions"], dtype=torch.float32, device=device).transpose(0, 1),
        "normal_hidden": torch.as_tensor(corpus["normal_initial_hidden"], dtype=torch.float32, device=device),
        "variant_hidden": torch.as_tensor(corpus["variant_initial_hidden"], dtype=torch.float32, device=device),
        "mask": torch.as_tensor(corpus["sequence_mask"], dtype=torch.float32, device=device).transpose(0, 1),
        "weights": torch.as_tensor(corpus["row_weight"], dtype=torch.float32, device=device),
        "lengths": torch.as_tensor(sequence_lengths(corpus["sequence_mask"]), dtype=torch.float32, device=device),
    }


def recurrent_logp_sums(model: ActorCritic, tensors: dict[str, torch.Tensor], hidden_key: str) -> torch.Tensor:
    dones = torch.zeros_like(tensors["mask"], dtype=torch.bool)
    logp, _entropy, _value = model.evaluate_actions_recurrent_sequence(
        tensors["obs"],
        tensors["actions"],
        tensors[hidden_key],
        dones,
    )
    return torch.sum(logp * tensors["mask"], dim=0)


def differentiable_temporal_loss(
    model: ActorCritic,
    tensors: dict[str, torch.Tensor],
    *,
    base_normal_logp: torch.Tensor,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> tuple[torch.Tensor, dict[str, torch.Tensor]]:
    normal_logp = recurrent_logp_sums(model, tensors, "normal_hidden")
    variant_logp = recurrent_logp_sums(model, tensors, "variant_hidden")
    lengths = tensors["lengths"]
    weights = tensors["weights"]
    denominator = torch.sum(weights)
    normal_nll = -normal_logp / lengths
    pref = torch.nn.functional.softplus((variant_logp - normal_logp) / lengths + float(preference_margin))
    anchor = torch.square((normal_logp - base_normal_logp) / lengths)
    weighted_normal = torch.sum(weights * normal_nll) / denominator
    weighted_pref = torch.sum(weights * pref) / denominator
    weighted_anchor = torch.sum(weights * anchor) / denominator
    total = weighted_normal + float(lambda_pref) * weighted_pref + float(lambda_anchor) * weighted_anchor
    return total, {
        "weighted_normal_sequence_nll": weighted_normal.detach(),
        "weighted_temporal_preference_loss": weighted_pref.detach(),
        "weighted_base_logp_anchor": weighted_anchor.detach(),
        "weighted_total_loss": total.detach(),
        "weighted_logp_gap_mean": (torch.sum(weights * ((normal_logp - variant_logp) / lengths)) / denominator).detach(),
    }


def train_actor_mean_update(
    *,
    model: ActorCritic,
    tensors: dict[str, torch.Tensor],
    base_normal_logp: torch.Tensor,
    epochs: int,
    lr: float,
    seed: int,
    grad_clip_norm: float,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> list[dict[str, Any]]:
    torch.manual_seed(int(seed))
    set_actor_mean_trainable_only(model)
    optimizer = torch.optim.Adam(model.actor_mean.parameters(), lr=float(lr))
    rows: list[dict[str, Any]] = []
    for epoch in range(1, int(epochs) + 1):
        optimizer.zero_grad(set_to_none=True)
        loss, metrics = differentiable_temporal_loss(
            model,
            tensors,
            base_normal_logp=base_normal_logp,
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        if not torch.isfinite(loss):
            raise RuntimeError(f"non-finite M1002 loss at epoch {epoch}: {float(loss.detach().cpu())}")
        loss.backward()
        grad_norm = float(torch.nn.utils.clip_grad_norm_(model.actor_mean.parameters(), float(grad_clip_norm)).detach().cpu().item())
        optimizer.step()
        if epoch == 1 or epoch == int(epochs) or epoch % max(1, int(epochs) // 20) == 0:
            rows.append(
                {
                    "epoch": int(epoch),
                    "loss": float(loss.detach().cpu().item()),
                    "grad_norm": grad_norm,
                    **{name: float(value.cpu().item()) for name, value in metrics.items()},
                }
            )
    return rows


def deterministic_action_drift(
    *,
    model: ActorCritic,
    corpus: dict[str, np.ndarray],
    device: torch.device,
) -> dict[str, float]:
    observations = np.asarray(corpus["normal_rollout_observations"], dtype=np.float32)
    reference_actions = np.asarray(corpus["normal_rollout_actions"], dtype=np.float32)
    masks = np.asarray(corpus["sequence_mask"], dtype=bool)
    hiddens = np.asarray(corpus["normal_initial_hidden"], dtype=np.float32)
    distances: list[float] = []
    for row_idx in range(observations.shape[0]):
        hidden = torch.as_tensor(hiddens[row_idx], dtype=torch.float32, device=device).unsqueeze(0)
        for step_idx in range(observations.shape[1]):
            if not bool(masks[row_idx, step_idx]):
                break
            action, hidden = deterministic_action_from_hidden(
                model,
                observations[row_idx, step_idx],
                hidden,
                device,
            )
            distances.append(float(np.linalg.norm(action - reference_actions[row_idx, step_idx])))
    if not distances:
        return {"candidate_action_l2_mean": float("nan"), "candidate_action_l2_max": float("nan")}
    return {
        "candidate_action_l2_mean": float(np.mean(distances)),
        "candidate_action_l2_max": float(np.max(distances)),
    }


def evaluate_state_exact(
    *,
    model: ActorCritic,
    state: dict[str, torch.Tensor],
    corpus: dict[str, np.ndarray],
    tensors: dict[str, torch.Tensor],
    base_normal_logp: torch.Tensor,
    base_metrics: dict[str, float],
    device: torch.device,
    alpha: float | None,
    candidate: str,
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> dict[str, Any]:
    model.load_state_dict({name: tensor.to(device=device) for name, tensor in state.items()})
    model.eval()
    with torch.no_grad():
        normal_logp = recurrent_logp_sums(model, tensors, "normal_hidden").detach().cpu().numpy().astype(np.float32)
        variant_logp = recurrent_logp_sums(model, tensors, "variant_hidden").detach().cpu().numpy().astype(np.float32)
    lengths = sequence_lengths(corpus["sequence_mask"])
    weights = np.asarray(corpus["row_weight"], dtype=np.float32)
    normal_nll = -normal_logp / lengths
    pref = temporal_preference_loss(
        normal_logp=normal_logp,
        variant_on_normal_logp=variant_logp,
        lengths=lengths,
        margin=preference_margin,
    )
    base_logp_np = base_normal_logp.detach().cpu().numpy().astype(np.float32)
    anchor = np.square((normal_logp - base_logp_np) / lengths)
    logp_gap = (normal_logp - variant_logp) / lengths
    drift = deterministic_action_drift(model=model, corpus=corpus, device=device)
    weighted_normal = weighted_mean(normal_nll, weights)
    weighted_pref = weighted_mean(pref, weights)
    weighted_anchor = weighted_mean(anchor, weights)
    weighted_total = weighted_normal + float(lambda_pref) * weighted_pref + float(lambda_anchor) * weighted_anchor
    row = {
        "candidate": candidate,
        "alpha": "" if alpha is None else float(alpha),
        "weighted_total_loss": weighted_total,
        "weighted_normal_sequence_nll": weighted_normal,
        "weighted_temporal_preference_loss": weighted_pref,
        "weighted_base_logp_anchor": weighted_anchor,
        "weighted_logp_gap_mean": weighted_mean(logp_gap, weights),
        "temporal_logp_gap_p10": float(np.quantile(logp_gap, 0.10)),
        "temporal_logp_gap_p50": float(np.quantile(logp_gap, 0.50)),
        "temporal_logp_gap_p90": float(np.quantile(logp_gap, 0.90)),
        **drift,
    }
    row["total_loss_improvement"] = float(base_metrics["weighted_total_loss"] - weighted_total)
    row["normal_nll_regression"] = float(weighted_normal - base_metrics["weighted_normal_sequence_nll"])
    row["pref_loss_regression"] = float(weighted_pref - base_metrics["weighted_temporal_preference_loss"])
    row["gap_regression"] = float(base_metrics["weighted_logp_gap_mean"] - row["weighted_logp_gap_mean"])
    row["gap_p10_regression"] = float(base_metrics["temporal_logp_gap_p10"] - row["temporal_logp_gap_p10"])
    row["total_loss_pass"] = bool(weighted_total <= base_metrics["weighted_total_loss"] - 0.001)
    row["normal_nll_pass"] = bool(weighted_normal <= base_metrics["weighted_normal_sequence_nll"] + 0.005)
    row["pref_loss_pass"] = bool(weighted_pref <= base_metrics["weighted_temporal_preference_loss"] + 0.005)
    row["gap_pass"] = bool(row["weighted_logp_gap_mean"] >= base_metrics["weighted_logp_gap_mean"] - 0.050)
    row["gap_p10_pass"] = bool(row["temporal_logp_gap_p10"] >= base_metrics["temporal_logp_gap_p10"] - 0.020)
    row["action_mean_pass"] = bool(row["candidate_action_l2_mean"] <= 0.015)
    row["action_max_pass"] = bool(row["candidate_action_l2_max"] <= 0.080)
    row["exact_gate_pass"] = bool(
        row["total_loss_pass"]
        and row["normal_nll_pass"]
        and row["pref_loss_pass"]
        and row["gap_pass"]
        and row["gap_p10_pass"]
        and row["action_mean_pass"]
        and row["action_max_pass"]
    )
    return row


def run_temporal_sequence_update_probe(
    *,
    checkpoint_path: Path,
    corpus_path: Path,
    metadata_path: Path,
    base_summary_path: Path,
    run_dir: Path,
    device: str,
    epochs: int,
    seed: int,
    lr: float,
    grad_clip_norm: float,
    alphas: tuple[float, ...],
    preference_margin: float,
    lambda_pref: float,
    lambda_anchor: float,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    resolved_device = resolve_device(device)
    model, checkpoint_data = load_actor_critic_checkpoint(checkpoint_path, device=str(resolved_device))
    model.eval()
    corpus = load_corpus(corpus_path)
    metadata = pd.read_csv(metadata_path)
    tensors = tensors_from_corpus(corpus, resolved_device)
    base_state = clone_state_dict(model)
    base_checksum = state_checksum(base_state)
    base_non_actor_checksum = state_checksum(base_state, exclude_actor_mean=True)
    with torch.no_grad():
        base_normal_logp = recurrent_logp_sums(model, tensors, "normal_hidden").detach()
    base_metrics = {
        "weighted_total_loss": float(pd.read_json(base_summary_path, typ="series")["weighted_total_loss"]),
        "weighted_normal_sequence_nll": float(pd.read_json(base_summary_path, typ="series")["weighted_normal_sequence_nll"]),
        "weighted_temporal_preference_loss": float(
            pd.read_json(base_summary_path, typ="series")["weighted_temporal_preference_loss"]
        ),
        "weighted_logp_gap_mean": float(pd.read_json(base_summary_path, typ="series")["weighted_logp_gap_mean"]),
        "temporal_logp_gap_p10": float(pd.read_json(base_summary_path, typ="series")["temporal_logp_gap_p10"]),
    }
    train_rows = train_actor_mean_update(
        model=model,
        tensors=tensors,
        base_normal_logp=base_normal_logp,
        epochs=epochs,
        lr=lr,
        seed=seed,
        grad_clip_norm=grad_clip_norm,
        preference_margin=preference_margin,
        lambda_pref=lambda_pref,
        lambda_anchor=lambda_anchor,
    )
    raw_state = clone_state_dict(model)
    raw_changed = changed_parameter_names(base_state, raw_state)
    raw_non_actor_checksum = state_checksum(raw_state, exclude_actor_mean=True)
    raw_actor_mean_changed = any(name.startswith(ACTOR_MEAN_PREFIX) for name in raw_changed)
    raw_non_actor_changed = bool(base_non_actor_checksum != raw_non_actor_checksum)
    checkpoint_dir = run_dir / "checkpoints"
    _save_checkpoint(
        checkpoint_data=checkpoint_data,
        state_dict=raw_state,
        destination=checkpoint_dir / "raw_actor_mean_update.pt",
        objective="temporal_sequence_objective_update_probe_raw",
    )

    interpolation_rows: list[dict[str, Any]] = []
    candidate_checkpoint_rows: list[dict[str, Any]] = []
    for alpha in alphas:
        candidate_state = interpolate_actor_mean_state(base_state, raw_state, float(alpha))
        row = evaluate_state_exact(
            model=model,
            state=candidate_state,
            corpus=corpus,
            tensors=tensors,
            base_normal_logp=base_normal_logp,
            base_metrics=base_metrics,
            device=resolved_device,
            alpha=float(alpha),
            candidate="interpolation",
            preference_margin=preference_margin,
            lambda_pref=lambda_pref,
            lambda_anchor=lambda_anchor,
        )
        interpolation_rows.append(row)
        if bool(row["exact_gate_pass"]):
            path = checkpoint_dir / f"alpha_{str(float(alpha)).replace('.', '_')}.pt"
            _save_checkpoint(
                checkpoint_data=checkpoint_data,
                state_dict=candidate_state,
                destination=path,
                objective="temporal_sequence_objective_update_probe_candidate",
            )
            candidate_checkpoint_rows.append({"alpha": float(alpha), "checkpoint": path})
    candidate_rows = [row for row in interpolation_rows if bool(row["exact_gate_pass"])]
    best_candidate = (
        sorted(candidate_rows, key=lambda row: (float(row["weighted_total_loss"]), float(row["candidate_action_l2_mean"])))[0]
        if candidate_rows
        else {}
    )
    result_class = (
        "temporal_sequence_update_exact_candidate"
        if candidate_rows and raw_actor_mean_changed and not raw_non_actor_changed
        else "temporal_sequence_update_no_exact_candidate"
    )
    write_csv_rows(run_dir / "train_history.csv", train_rows)
    write_csv_rows(run_dir / "interpolation_metrics.csv", interpolation_rows)
    write_csv_rows(run_dir / "candidate_checkpoints.csv", candidate_checkpoint_rows)
    summary = {
        "run_type": "capability_step_temporal_sequence_update_probe",
        "checkpoint": checkpoint_path,
        "corpus": corpus_path,
        "metadata": metadata_path,
        "base_summary": base_summary_path,
        "row_count": int(corpus["sequence_mask"].shape[0]),
        "positive_row_count": int(metadata["positive_target"].astype(bool).sum()) if "positive_target" in metadata else int(len(metadata)),
        "epochs": int(epochs),
        "seed": int(seed),
        "lr": float(lr),
        "grad_clip_norm": float(grad_clip_norm),
        "interpolation_alphas": list(alphas),
        "preference_margin": float(preference_margin),
        "lambda_pref": float(lambda_pref),
        "lambda_anchor": float(lambda_anchor),
        "base_checksum": base_checksum,
        "raw_changed_parameter_names": raw_changed,
        "raw_actor_mean_changed": raw_actor_mean_changed,
        "raw_non_actor_changed": raw_non_actor_changed,
        "exact_candidate_count": int(len(candidate_rows)),
        "best_candidate": best_candidate,
        "result_class": result_class,
        "candidate_checkpoints": candidate_checkpoint_rows,
        "train_history_csv": run_dir / "train_history.csv",
        "interpolation_metrics_csv": run_dir / "interpolation_metrics.csv",
        "candidate_checkpoints_csv": run_dir / "candidate_checkpoints.csv",
        "raw_checkpoint": checkpoint_dir / "raw_actor_mean_update.pt",
        "training_started": True,
        "ppo_used": False,
        "promoted": False,
    }
    write_json(run_dir / "summary.json", summary)
    if raw_non_actor_changed:
        raise RuntimeError(f"M1002 changed non-actor_mean parameters: {raw_changed}")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run exact actor_mean-only temporal sequence update probe.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--base-summary", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--epochs", type=int, default=200)
    parser.add_argument("--seed", type=int, default=1002)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--grad-clip-norm", type=float, default=1.0)
    parser.add_argument("--alphas", type=parse_alphas, default=DEFAULT_ALPHAS)
    parser.add_argument("--preference-margin", type=float, default=0.05)
    parser.add_argument("--lambda-pref", type=float, default=1.0)
    parser.add_argument("--lambda-anchor", type=float, default=0.25)
    args = parser.parse_args()
    run_dir = args.run_dir or make_run_dir(prefix="temporal_sequence_update_probe")
    summary = run_temporal_sequence_update_probe(
        checkpoint_path=args.checkpoint,
        corpus_path=args.corpus,
        metadata_path=args.metadata,
        base_summary_path=args.base_summary,
        run_dir=run_dir,
        device=args.device,
        epochs=args.epochs,
        seed=args.seed,
        lr=args.lr,
        grad_clip_norm=args.grad_clip_norm,
        alphas=tuple(args.alphas),
        preference_margin=args.preference_margin,
        lambda_pref=args.lambda_pref,
        lambda_anchor=args.lambda_anchor,
    )
    print(pd.Series(summary).to_string())
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
