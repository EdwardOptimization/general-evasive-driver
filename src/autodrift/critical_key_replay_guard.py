"""Replay protected rollout keys before expensive strict proof-surface miners."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from autodrift.artifacts import make_run_dir, read_json, to_jsonable, write_json
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.env import AutoDriftEnv
from autodrift.evaluate import load_env_config
from autodrift.outcome_sensitive_corpus import ProbeConfig
from autodrift.snapshot_bank_relocation import run_snapshot_bank_relocation


@dataclass(frozen=True)
class CheckpointPolicy:
    name: str
    path: Path


@dataclass(frozen=True)
class ProtectedCase:
    seed: int
    source_condition: str
    source_step: int
    paired_step: int
    target_obstacle_distance: float
    relocated_obstacle_body_y: float
    relocated_obstacle_half_width: float
    reference_normal_margin: float
    reference_wrong_history_margin: float
    reference_margin_gap: float

    @property
    def key(self) -> str:
        return f"{self.seed}|{self.source_condition}|{self.source_step}|{self.paired_step}"


def parse_checkpoint_policy(spec: str) -> CheckpointPolicy:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"checkpoint policy must be NAME=PATH, got {spec!r}")
    name, raw_path = spec.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError(f"checkpoint policy has empty name: {spec!r}")
    if not raw_path.strip():
        raise argparse.ArgumentTypeError(f"checkpoint policy has empty path: {spec!r}")
    return CheckpointPolicy(name=name, path=Path(raw_path))


def _bool_value(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _finite_float(value: Any, default: float = float("nan")) -> float:
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    return output if np.isfinite(output) else default


def _case_key(seed: int, source_condition: str, source_step: int, paired_step: int) -> str:
    return f"{int(seed)}|{source_condition}|{int(source_step)}|{int(paired_step)}"


def derive_protected_cases(reference_frames: list[pd.DataFrame], case_keys: set[str] | None = None) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for frame in reference_frames:
        for _, row in frame.iterrows():
            for source_condition, paired_condition in (("nominal", "perturbed"), ("perturbed", "nominal")):
                if not _bool_value(row.get(f"{source_condition}_accepted_outcome_sensitive", False)):
                    continue
                seed = int(row["seed"])
                source_step = int(row[f"{source_condition}_step"])
                paired_step = int(row[f"{paired_condition}_step"])
                key = _case_key(seed, source_condition, source_step, paired_step)
                if case_keys and key not in case_keys:
                    continue
                exact_key = (
                    key,
                    round(_finite_float(row["target_obstacle_distance"]), 9),
                    round(_finite_float(row["relocated_obstacle_body_y"]), 9),
                    round(_finite_float(row["relocated_obstacle_half_width"]), 9),
                )
                if exact_key in seen:
                    continue
                seen.add(exact_key)
                protected_case = ProtectedCase(
                    seed=seed,
                    source_condition=source_condition,
                    source_step=source_step,
                    paired_step=paired_step,
                    target_obstacle_distance=_finite_float(row["target_obstacle_distance"]),
                    relocated_obstacle_body_y=_finite_float(row["relocated_obstacle_body_y"]),
                    relocated_obstacle_half_width=_finite_float(row["relocated_obstacle_half_width"]),
                    reference_normal_margin=_finite_float(row.get(f"{source_condition}_normal_margin")),
                    reference_wrong_history_margin=_finite_float(
                        row.get(f"{source_condition}_wrong_history_margin")
                    ),
                    reference_margin_gap=_finite_float(row.get(f"{source_condition}_margin_gap")),
                )
                rows.append({"key": protected_case.key, **asdict(protected_case)})
    if not rows:
        raise ValueError("no protected cases matched the requested keys")
    return pd.DataFrame(rows)


def _case_from_row(row: pd.Series) -> ProtectedCase:
    return ProtectedCase(
        seed=int(row["seed"]),
        source_condition=str(row["source_condition"]),
        source_step=int(row["source_step"]),
        paired_step=int(row["paired_step"]),
        target_obstacle_distance=float(row["target_obstacle_distance"]),
        relocated_obstacle_body_y=float(row["relocated_obstacle_body_y"]),
        relocated_obstacle_half_width=float(row["relocated_obstacle_half_width"]),
        reference_normal_margin=float(row["reference_normal_margin"]),
        reference_wrong_history_margin=float(row["reference_wrong_history_margin"]),
        reference_margin_gap=float(row["reference_margin_gap"]),
    )


def _candidate_subset(candidates: pd.DataFrame, case: ProtectedCase) -> pd.DataFrame:
    source_step_column = f"{case.source_condition}_step"
    paired_condition = "perturbed" if case.source_condition == "nominal" else "nominal"
    paired_step_column = f"{paired_condition}_step"
    mask = (
        candidates["seed"].eq(case.seed)
        & np.isclose(candidates["target_obstacle_distance"].astype(float), case.target_obstacle_distance)
        & np.isclose(candidates["relocated_obstacle_body_y"].astype(float), case.relocated_obstacle_body_y)
        & np.isclose(candidates["relocated_obstacle_half_width"].astype(float), case.relocated_obstacle_half_width)
        & candidates[source_step_column].astype(int).eq(case.source_step)
        & candidates[paired_step_column].astype(int).eq(case.paired_step)
    )
    return candidates.loc[mask].copy()


def evaluate_protected_cases(
    candidates: pd.DataFrame,
    protected_cases: pd.DataFrame,
    *,
    policy: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, case_row in protected_cases.iterrows():
        case = _case_from_row(case_row)
        subset = _candidate_subset(candidates, case)
        source = case.source_condition
        accepted_column = f"{source}_accepted_outcome_sensitive"
        normal_margin_column = f"{source}_normal_margin"
        wrong_margin_column = f"{source}_wrong_history_margin"
        margin_gap_column = f"{source}_margin_gap"
        normal_success_column = f"{source}_normal_success"
        accepted = False
        selected: pd.Series | None = None
        if len(subset):
            accepted_mask = subset[accepted_column].map(_bool_value)
            accepted = bool(accepted_mask.any())
            ranking = subset.assign(_guard_margin_gap=subset[margin_gap_column].astype(float))
            selected = ranking.sort_values("_guard_margin_gap", ascending=False).iloc[0]
        rows.append(
            {
                "policy": policy,
                "key": case.key,
                "seed": case.seed,
                "source_condition": case.source_condition,
                "source_step": case.source_step,
                "paired_step": case.paired_step,
                "target_obstacle_distance": case.target_obstacle_distance,
                "relocated_obstacle_body_y": case.relocated_obstacle_body_y,
                "relocated_obstacle_half_width": case.relocated_obstacle_half_width,
                "reference_normal_margin": case.reference_normal_margin,
                "reference_wrong_history_margin": case.reference_wrong_history_margin,
                "reference_margin_gap": case.reference_margin_gap,
                "found_rows": int(len(subset)),
                "accepted": accepted,
                "normal_success": (
                    _bool_value(selected.get(normal_success_column)) if selected is not None else False
                ),
                "normal_margin": (
                    _finite_float(selected.get(normal_margin_column)) if selected is not None else float("nan")
                ),
                "wrong_history_margin": (
                    _finite_float(selected.get(wrong_margin_column)) if selected is not None else float("nan")
                ),
                "margin_gap": (
                    _finite_float(selected.get(margin_gap_column)) if selected is not None else float("nan")
                ),
                "margin_gap_delta_vs_reference": (
                    _finite_float(selected.get(margin_gap_column)) - case.reference_margin_gap
                    if selected is not None
                    else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def _tuple_range(value: Any) -> tuple[float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise ValueError(f"expected two-value range, got {value!r}")
    return (float(value[0]), float(value[1]))


def _randomization(raw: Any) -> dict[str, tuple[float, float]]:
    output: dict[str, tuple[float, float]] = {}
    for key, value in (raw or {}).items():
        output[str(key)] = _tuple_range(value)
    return output


def _float_list(values: pd.Series) -> list[float]:
    return sorted({float(value) for value in values.tolist()})


def run_guard(
    *,
    reference_manifest: Path,
    reference_cases_csv: list[Path],
    checkpoint_policies: list[CheckpointPolicy],
    case_keys: set[str] | None,
    reference_policy: str | None,
    device: str,
    run_dir: Path,
) -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame]:
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = read_json(reference_manifest)
    reference_frames = [pd.read_csv(path) for path in reference_cases_csv]
    protected_cases = derive_protected_cases(reference_frames, case_keys=case_keys)
    protected_cases.to_csv(run_dir / "protected_cases.csv", index=False)

    base_config = load_env_config(Path(manifest["env_config"]))
    target_obs_dim = int(AutoDriftEnv(base_config).observation_space.shape[0])
    seeds = sorted({int(seed) for seed in protected_cases["seed"].tolist()})
    probe = manifest.get("probe", {})
    probe_config = ProbeConfig(
        strategy=str(probe.get("strategy", "steer_brake")),
        steer_amplitude=float(probe.get("steer_amplitude", 0.25)),
        brake_level=float(probe.get("brake_level", 0.20)),
        throttle_level=float(probe.get("throttle_level", 0.0)),
        period_steps=int(probe.get("period_steps", 20)),
        until_step=probe.get("until_step"),
        until_distance=probe.get("until_distance"),
    )

    all_results: list[pd.DataFrame] = []
    summaries: list[dict[str, Any]] = []
    candidate_artifacts: dict[str, str] = {}
    for policy in checkpoint_policies:
        model, _ = load_actor_critic_checkpoint(policy.path, device=device, obs_dim=target_obs_dim)
        candidates, _, _, summary, _, _ = run_snapshot_bank_relocation(
            model=model,
            base_config=base_config,
            seeds=seeds,
            nominal_friction_mu_range=_tuple_range(manifest["nominal_friction_mu_range"]),
            perturbed_friction_mu_range=_tuple_range(manifest["perturbed_friction_mu_range"]),
            nominal_randomization=_randomization(manifest.get("nominal_randomization")),
            perturbed_randomization=_randomization(manifest.get("perturbed_randomization")),
            obstacle_perception_reveal_step=manifest.get("obstacle_perception_reveal_step"),
            obstacle_perception_reveal_distance=manifest.get("obstacle_perception_reveal_distance"),
            bank_obstacle_distance_range=_tuple_range(manifest["bank_obstacle_distance_range"]),
            bank_stride_steps=int(manifest["bank_stride_steps"]),
            bank_max_snapshots=int(manifest["bank_max_snapshots"]),
            bank_max_pairs_per_seed=int(manifest["bank_max_pairs_per_seed"]),
            max_pre_visible_distance=manifest.get("max_pre_visible_distance"),
            max_pre_response_distance=manifest.get("max_pre_response_distance"),
            max_pre_context_distance=manifest.get("max_pre_context_distance"),
            snapshot_relocation_distances=_float_list(protected_cases["target_obstacle_distance"]),
            snapshot_relocation_lateral_offsets=_float_list(protected_cases["relocated_obstacle_body_y"]),
            snapshot_relocation_half_widths=_float_list(protected_cases["relocated_obstacle_half_width"]),
            min_probe_steps=int(manifest["min_probe_steps"]),
            max_probe_steps=int(manifest["max_probe_steps"]),
            require_friction_step=bool(manifest["require_friction_step"]),
            min_hidden_updates_after_friction=int(manifest["min_hidden_updates_after_friction"]),
            max_visible_distance=float(manifest["max_visible_distance"]),
            max_response_distance=manifest.get("max_response_distance"),
            max_context_distance=manifest.get("max_context_distance"),
            min_margin_gap=float(manifest["min_margin_gap"]),
            min_normal_margin=manifest.get("min_normal_margin"),
            max_normal_margin=manifest.get("max_normal_margin"),
            require_normal_success=bool(manifest["require_normal_success"]),
            max_continuation_steps=manifest.get("max_continuation_steps"),
            top_k=int(manifest.get("top_k", 200)),
            max_selected_per_physical_pair=int(manifest.get("max_selected_per_physical_pair", 1)),
            max_selected_per_seed=int(manifest.get("max_selected_per_seed", 2)),
            probe_config=probe_config,
            outcome_export_min_margin_gap=float(manifest["outcome_export"]["min_margin_gap"]),
            outcome_export_boundary_margin_scale=float(manifest["outcome_export"]["boundary_margin_scale"]),
            export_only_accepted_outcomes=bool(manifest["outcome_export"]["only_accepted_outcomes"]),
        )
        candidates_path = run_dir / f"{policy.name}_candidates.csv"
        candidates.to_csv(candidates_path, index=False)
        candidate_artifacts[policy.name] = str(candidates_path)
        result = evaluate_protected_cases(candidates, protected_cases, policy=policy.name)
        all_results.append(result)
        summaries.append(
            {
                "policy": policy.name,
                "checkpoint": str(policy.path),
                "cases": int(len(result)),
                "accepted_cases": int(result["accepted"].sum()),
                "policy_pass": bool(result["accepted"].all()),
                "candidate_rows": int(len(candidates)),
                "outcome_sensitive_pairs": (
                    int(summary.iloc[0]["accepted_outcome_sensitive_pairs"]) if len(summary) else 0
                ),
            }
        )

    guard_results = pd.concat(all_results, ignore_index=True)
    policy_summary = pd.DataFrame(summaries)
    guard_results.to_csv(run_dir / "guard_results.csv", index=False)
    policy_summary.to_csv(run_dir / "policy_summary.csv", index=False)

    reference_name = reference_policy or checkpoint_policies[0].name
    reference_rows = policy_summary.loc[policy_summary["policy"].eq(reference_name)]
    if reference_rows.empty:
        raise ValueError(f"reference policy {reference_name!r} was not evaluated")
    reference_reproduced = bool(reference_rows.iloc[0]["policy_pass"])
    non_reference = policy_summary.loc[~policy_summary["policy"].eq(reference_name)]
    rejected_non_reference = int((~non_reference["policy_pass"]).sum()) if len(non_reference) else 0
    summary = {
        "run_type": "critical_key_replay_guard",
        "reference_manifest": reference_manifest,
        "reference_cases_csv": reference_cases_csv,
        "checkpoint_policies": [asdict(policy) for policy in checkpoint_policies],
        "reference_policy": reference_name,
        "protected_cases": int(len(protected_cases)),
        "reference_reproduced": reference_reproduced,
        "rejected_non_reference_policies": rejected_non_reference,
        "guard_validated": bool(reference_reproduced and rejected_non_reference > 0),
        "protected_cases_csv": run_dir / "protected_cases.csv",
        "guard_results_csv": run_dir / "guard_results.csv",
        "policy_summary_csv": run_dir / "policy_summary.csv",
        "candidate_artifacts": candidate_artifacts,
    }
    write_json(run_dir / "summary.json", summary)
    write_json(
        run_dir / "manifest.json",
        {
            **summary,
            "case_keys": sorted(case_keys) if case_keys else [],
            "device": device,
        },
    )
    return summary, guard_results, policy_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay protected strict proof-surface keys.")
    parser.add_argument("--reference-manifest", type=Path, required=True)
    parser.add_argument("--reference-cases-csv", type=Path, action="append", required=True)
    parser.add_argument("--checkpoint-policy", type=parse_checkpoint_policy, action="append", required=True)
    parser.add_argument("--case-key", action="append", default=[])
    parser.add_argument("--reference-policy", type=str, default=None)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="critical_key_replay_guard")
    summary, _, policy_summary = run_guard(
        reference_manifest=args.reference_manifest,
        reference_cases_csv=args.reference_cases_csv,
        checkpoint_policies=args.checkpoint_policy,
        case_keys=set(args.case_key) if args.case_key else None,
        reference_policy=args.reference_policy,
        device=args.device,
        run_dir=run_dir,
    )
    print(policy_summary.to_string(index=False))
    print(f"guard_validated={summary['guard_validated']}")
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
