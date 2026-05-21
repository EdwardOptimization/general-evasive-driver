"""Checkpoint interpolation utilities for trust-region policy probes."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from pathlib import Path
from typing import Any

import torch

from autodrift.artifacts import make_run_dir, to_jsonable, write_json
from autodrift.checkpoints import REQUIRED_MODEL_CONFIG_KEYS


def _load_checkpoint(path: Path) -> dict[str, Any]:
    checkpoint = torch.load(path, map_location="cpu")
    if "model_state" not in checkpoint:
        raise ValueError(f"checkpoint is missing model_state: {path}")
    if "config" not in checkpoint:
        raise ValueError(f"checkpoint is missing config: {path}")
    return checkpoint


def _validate_alpha(alpha: float) -> float:
    value = float(alpha)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"alpha must be in [0, 1], got {alpha}")
    return value


def _validate_model_config_compatibility(base_config: dict[str, Any], target_config: dict[str, Any]) -> None:
    mismatches = []
    for key in REQUIRED_MODEL_CONFIG_KEYS:
        if key in base_config and key in target_config and base_config[key] != target_config[key]:
            mismatches.append((key, base_config[key], target_config[key]))
    if mismatches:
        formatted = ", ".join(f"{key}: {base!r} != {target!r}" for key, base, target in mismatches)
        raise ValueError(f"checkpoint model configs are incompatible: {formatted}")


def interpolate_model_states(
    base_state: dict[str, torch.Tensor],
    target_state: dict[str, torch.Tensor],
    *,
    alpha: float,
) -> dict[str, torch.Tensor]:
    """Linearly interpolate compatible model states.

    ``alpha=0`` returns the base state and ``alpha=1`` returns the target state.
    Non-floating tensors are copied only when both sources are exactly equal.
    """

    value = _validate_alpha(alpha)
    base_keys = set(base_state)
    target_keys = set(target_state)
    missing = sorted(base_keys.difference(target_keys))
    unexpected = sorted(target_keys.difference(base_keys))
    if missing or unexpected:
        raise ValueError(f"model_state keys differ: missing={missing}, unexpected={unexpected}")

    output: dict[str, torch.Tensor] = {}
    for key in sorted(base_state):
        base_tensor = base_state[key].detach().cpu()
        target_tensor = target_state[key].detach().cpu()
        if tuple(base_tensor.shape) != tuple(target_tensor.shape):
            raise ValueError(
                f"model_state tensor shape mismatch for {key}: "
                f"{tuple(base_tensor.shape)} != {tuple(target_tensor.shape)}"
            )
        if base_tensor.dtype != target_tensor.dtype:
            raise ValueError(f"model_state tensor dtype mismatch for {key}: {base_tensor.dtype} != {target_tensor.dtype}")
        if torch.is_floating_point(base_tensor):
            output[key] = (base_tensor + (target_tensor - base_tensor) * value).clone()
        else:
            if not torch.equal(base_tensor, target_tensor):
                raise ValueError(f"non-floating model_state tensor differs for {key}")
            output[key] = base_tensor.clone()
    return output


def write_interpolated_checkpoint(
    *,
    base_checkpoint_path: Path | str,
    target_checkpoint_path: Path | str,
    output_path: Path | str,
    alpha: float,
    base_label: str = "base",
    target_label: str = "target",
    policy_label: str | None = None,
) -> dict[str, Any]:
    base_path = Path(base_checkpoint_path)
    target_path = Path(target_checkpoint_path)
    destination = Path(output_path)
    base_checkpoint = _load_checkpoint(base_path)
    target_checkpoint = _load_checkpoint(target_path)
    _validate_model_config_compatibility(base_checkpoint["config"], target_checkpoint["config"])

    interpolated_state = interpolate_model_states(
        base_checkpoint["model_state"],
        target_checkpoint["model_state"],
        alpha=alpha,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    metadata = deepcopy(base_checkpoint.get("metadata", {}))
    if not isinstance(metadata, dict):
        metadata = {"base_metadata": metadata}
    alpha_value = _validate_alpha(alpha)
    metadata["interpolation"] = {
        "alpha": alpha_value,
        "base_checkpoint": str(base_path),
        "base_label": base_label,
        "target_checkpoint": str(target_path),
        "target_label": target_label,
        "policy_label": policy_label,
    }
    output_checkpoint = {
        "model_state": interpolated_state,
        "config": deepcopy(base_checkpoint["config"]),
        "metadata": to_jsonable(metadata),
    }
    torch.save(output_checkpoint, destination)
    return {
        "policy_label": policy_label,
        "alpha": alpha_value,
        "path": str(destination),
        "base_checkpoint": str(base_path),
        "target_checkpoint": str(target_path),
    }


def _alpha_file_token(alpha: float) -> str:
    text = f"{float(alpha):.3f}".rstrip("0").rstrip(".")
    return text.replace(".", "_")


def _alpha_label_token(alpha: float) -> str:
    return f"{int(round(float(alpha) * 1000.0)):03d}"


def write_interpolation_sweep(
    *,
    run_dir: Path | str,
    base_checkpoint_path: Path | str,
    target_checkpoint_path: Path | str,
    alphas: list[float],
    base_label: str = "base",
    target_label: str = "target",
    label_prefix: str = "interp",
) -> dict[str, Any]:
    output = Path(run_dir)
    checkpoint_dir = output / "checkpoints"
    rows = []
    for alpha in alphas:
        alpha_value = _validate_alpha(alpha)
        label = f"{label_prefix}_a{_alpha_label_token(alpha_value)}"
        checkpoint_path = checkpoint_dir / f"alpha_{_alpha_file_token(alpha_value)}.pt"
        rows.append(
            write_interpolated_checkpoint(
                base_checkpoint_path=base_checkpoint_path,
                target_checkpoint_path=target_checkpoint_path,
                output_path=checkpoint_path,
                alpha=alpha_value,
                base_label=base_label,
                target_label=target_label,
                policy_label=label,
            )
        )

    output.mkdir(parents=True, exist_ok=True)
    with (output / "checkpoint_policies.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["policy_label", "alpha", "path", "base_checkpoint", "target_checkpoint"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    policy_args = "\n".join(f"--checkpoint-policy {row['policy_label']}={row['path']}" for row in rows) + "\n"
    (output / "checkpoint_policy_args.txt").write_text(policy_args, encoding="utf-8")

    manifest = {
        "base_checkpoint": str(base_checkpoint_path),
        "base_label": base_label,
        "target_checkpoint": str(target_checkpoint_path),
        "target_label": target_label,
        "label_prefix": label_prefix,
        "count": len(rows),
        "checkpoints": rows,
    }
    write_json(output / "manifest.json", manifest)
    return manifest


def _parse_alphas(values: list[str]) -> list[float]:
    alphas: list[float] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                alphas.append(_validate_alpha(float(item)))
    if not alphas:
        raise ValueError("at least one alpha is required")
    return alphas


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-checkpoint", type=Path, required=True)
    parser.add_argument("--target-checkpoint", type=Path, required=True)
    parser.add_argument("--alphas", nargs="+", required=True, help="alpha values, space or comma separated")
    parser.add_argument("--base-label", default="base")
    parser.add_argument("--target-label", default="target")
    parser.add_argument("--label-prefix", default="interp")
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_arg_parser().parse_args(argv)
    run_dir = args.run_dir or make_run_dir(prefix="checkpoint_interpolation")
    manifest = write_interpolation_sweep(
        run_dir=run_dir,
        base_checkpoint_path=args.base_checkpoint,
        target_checkpoint_path=args.target_checkpoint,
        alphas=_parse_alphas(args.alphas),
        base_label=args.base_label,
        target_label=args.target_label,
        label_prefix=args.label_prefix,
    )
    print(f"wrote {manifest['count']} interpolated checkpoints to {run_dir}")


if __name__ == "__main__":
    main()
