"""Materialize selected M1013 exact candidates and run M267/M264 preflight."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from autodrift.artifacts import write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.capability_step_temporal_sequence_update_probe import (
    changed_parameter_names,
    clone_state_dict,
    interpolate_actor_mean_state,
    state_checksum,
    _save_checkpoint,
)
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG, _actor_inputs_changed


DEFAULT_BASE_CHECKPOINT = Path("runs/m974_exact_repair_from_base_s40_seed5974/candidate_checkpoint.pt")
DEFAULT_M267_CORPUS = Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")
DEFAULT_RUN_DIR = Path("runs/m1016_v4_public_base_m1013_exact_candidate_preflight")
BASE_POLICY_LABEL = "m974_base"


@dataclass(frozen=True)
class M1013CandidateSpec:
    name: str
    raw_checkpoint: Path
    alpha: float


DEFAULT_CANDIDATES: tuple[M1013CandidateSpec, ...] = (
    M1013CandidateSpec(
        name="m1013_lam0001_a020",
        raw_checkpoint=Path(
            "runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/"
            "checkpoints/lambda_0_001/raw_actor_mean_update.pt"
        ),
        alpha=0.2,
    ),
    M1013CandidateSpec(
        name="m1013_lam0030_a050",
        raw_checkpoint=Path(
            "runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/"
            "checkpoints/lambda_0_03/raw_actor_mean_update.pt"
        ),
        alpha=0.5,
    ),
    M1013CandidateSpec(
        name="m1013_lam0001_a050",
        raw_checkpoint=Path(
            "runs/m1013_v4_public_base_margin_weighted_branch_repair_update_probe/"
            "checkpoints/lambda_0_001/raw_actor_mean_update.pt"
        ),
        alpha=0.5,
    ),
)


def parse_candidate_spec(text: str) -> M1013CandidateSpec:
    parts = str(text).split(":")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("candidate spec must be name:raw_checkpoint:alpha")
    name, raw_checkpoint, alpha_text = parts
    if not name:
        raise argparse.ArgumentTypeError("candidate name must not be empty")
    return M1013CandidateSpec(name=name, raw_checkpoint=Path(raw_checkpoint), alpha=float(alpha_text))


def materialize_candidate(
    *,
    base_checkpoint: Path,
    candidate: M1013CandidateSpec,
    output_path: Path,
) -> dict[str, Any]:
    base_model, base_checkpoint_data = load_actor_critic_checkpoint(base_checkpoint, device="cpu")
    raw_model, _raw_checkpoint_data = load_actor_critic_checkpoint(candidate.raw_checkpoint, device="cpu")
    base_state = clone_state_dict(base_model)
    raw_state = clone_state_dict(raw_model)
    candidate_state = interpolate_actor_mean_state(base_state, raw_state, float(candidate.alpha))
    changed_names = changed_parameter_names(base_state, candidate_state)
    _save_checkpoint(
        checkpoint_data=base_checkpoint_data,
        state_dict=candidate_state,
        destination=output_path,
        objective="m1013_exact_candidate_preflight_materialized",
    )
    return {
        "candidate": candidate.name,
        "raw_checkpoint": candidate.raw_checkpoint,
        "alpha": float(candidate.alpha),
        "checkpoint": output_path,
        "changed_parameter_names": ";".join(changed_names),
        "non_actor_checksum_changed": bool(
            state_checksum(base_state, exclude_actor_mean=True) != state_checksum(candidate_state, exclude_actor_mean=True)
        ),
    }


def _failed_success_drop_rows(gate_dir: Path, candidate_label: str) -> str:
    rows_path = gate_dir / "boundary_replay_rows.csv"
    if not rows_path.exists():
        return ""
    frame = pd.read_csv(rows_path)
    if "policy" not in frame.columns or "success_drop" not in frame.columns:
        return ""
    candidate_rows = frame[frame["policy"].astype(str) == str(candidate_label)].copy()
    failed = candidate_rows[~candidate_rows["success_drop"].astype(bool)]["row_id"].astype(int).tolist()
    return ";".join(str(row_id) for row_id in sorted(failed))


def classify_m1013_preflight(
    *,
    materialization_contract_pass: bool,
    candidate_a_pass: bool,
    any_candidate_pass: bool,
    b_or_c_pass_without_a: bool,
    training_started: bool,
    ppo_used: bool,
    promoted: bool,
) -> str:
    if not bool(materialization_contract_pass) or bool(training_started) or bool(ppo_used) or bool(promoted):
        return "m1013_exact_candidate_preflight_contract_artifact"
    if bool(candidate_a_pass):
        return "m1013_exact_candidate_preflight_candidate_a_pass_trust_threshold_conservative"
    if bool(b_or_c_pass_without_a):
        return "m1013_exact_candidate_preflight_metric_ordering_artifact"
    if not bool(any_candidate_pass):
        return "m1013_exact_candidate_preflight_all_selected_fail_trust_threshold_supported"
    return "m1013_exact_candidate_preflight_mixed"


def failure_types_for_result_class(result_class: str) -> list[str]:
    if result_class.endswith("_contract_artifact"):
        return ["contract_violation"]
    if result_class.endswith("_metric_ordering_artifact"):
        return ["metric_artifact"]
    if result_class.endswith("_all_selected_fail_trust_threshold_supported"):
        return ["proof_washout"]
    return ["none"]


def run_m1013_exact_candidate_preflight(
    *,
    base_checkpoint: Path,
    candidates: tuple[M1013CandidateSpec, ...],
    corpus_csv: Path,
    env_config_path: Path,
    run_dir: Path,
    device: str,
    max_continuation_steps: int,
) -> dict[str, Any]:
    run_dir.mkdir(parents=True, exist_ok=True)
    materialized_rows: list[dict[str, Any]] = []
    preflight_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_checkpoint = run_dir / "checkpoints" / f"{candidate.name}.pt"
        materialized = materialize_candidate(
            base_checkpoint=base_checkpoint,
            candidate=candidate,
            output_path=candidate_checkpoint,
        )
        actor_inputs_changed = _actor_inputs_changed(base_checkpoint, candidate_checkpoint)
        materialized["actor_inputs_changed"] = bool(actor_inputs_changed)
        materialized_rows.append(materialized)
        gate_dir = run_dir / "candidate_preflight" / candidate.name
        summary = run_boundary_outcome_replay_gate(
            checkpoint_specs=(
                CheckpointSpec(label=BASE_POLICY_LABEL, path=base_checkpoint),
                CheckpointSpec(label=candidate.name, path=candidate_checkpoint),
            ),
            corpus_csv=corpus_csv,
            env_config_path=env_config_path,
            max_rows=0,
            max_continuation_steps=max_continuation_steps,
            baseline_policy=BASE_POLICY_LABEL,
            candidate_policy=candidate.name,
            max_normal_success_drop=0.0,
            max_normal_margin_regression=0.005,
            max_margin_gap_regression=0.001,
            max_success_drop_count_regression=0,
            device=device,
            run_dir=gate_dir,
        )
        preflight_rows.append(
            {
                "candidate": candidate.name,
                "raw_checkpoint": str(candidate.raw_checkpoint),
                "alpha": float(candidate.alpha),
                "checkpoint": str(candidate_checkpoint),
                "run_dir": str(gate_dir),
                "actor_inputs_changed": bool(actor_inputs_changed),
                "non_actor_checksum_changed": bool(materialized["non_actor_checksum_changed"]),
                "baseline_success_drop_count": int(summary["baseline_success_drop_count"]),
                "candidate_success_drop_count": int(summary["candidate_success_drop_count"]),
                "success_drop_count_delta": int(summary["success_drop_count_delta"]),
                "failed_success_drop_rows": _failed_success_drop_rows(gate_dir, candidate.name),
                "normal_success_delta": float(summary["normal_success_delta"]),
                "normal_margin_mean_delta": float(summary["normal_margin_mean_delta"]),
                "margin_gap_mean_delta": float(summary["margin_gap_mean_delta"]),
                "max_normal_success_drop": float(summary["max_normal_success_drop"]),
                "max_normal_margin_regression": float(summary["max_normal_margin_regression"]),
                "max_margin_gap_regression": float(summary["max_margin_gap_regression"]),
                "max_success_drop_count_regression": int(summary["max_success_drop_count_regression"]),
                "gate_pass": bool(summary["gate_pass"]) and not bool(actor_inputs_changed),
            }
        )
    write_csv_rows(run_dir / "materialized_candidates.csv", materialized_rows)
    write_csv_rows(run_dir / "m267_preflight_summary.csv", preflight_rows)
    materialization_contract_pass = bool(
        all(not bool(row["non_actor_checksum_changed"]) and not bool(row["actor_inputs_changed"]) for row in materialized_rows)
    )
    by_name = {str(row["candidate"]): row for row in preflight_rows}
    candidate_a_pass = bool(by_name.get("m1013_lam0001_a020", {}).get("gate_pass", False))
    any_candidate_pass = bool(any(bool(row["gate_pass"]) for row in preflight_rows))
    b_or_c_pass_without_a = bool(not candidate_a_pass and any_candidate_pass)
    result_class = classify_m1013_preflight(
        materialization_contract_pass=materialization_contract_pass,
        candidate_a_pass=candidate_a_pass,
        any_candidate_pass=any_candidate_pass,
        b_or_c_pass_without_a=b_or_c_pass_without_a,
        training_started=False,
        ppo_used=False,
        promoted=False,
    )
    summary = {
        "run_type": "m1013_exact_candidate_preflight",
        "base_checkpoint": base_checkpoint,
        "corpus_csv": corpus_csv,
        "env_config": env_config_path,
        "max_continuation_steps": int(max_continuation_steps),
        "candidate_count": int(len(candidates)),
        "materialization_contract_pass": bool(materialization_contract_pass),
        "candidate_a_pass": bool(candidate_a_pass),
        "any_candidate_pass": bool(any_candidate_pass),
        "b_or_c_pass_without_a": bool(b_or_c_pass_without_a),
        "preflight_pass_count": int(sum(1 for row in preflight_rows if bool(row["gate_pass"]))),
        "result_class": result_class,
        "failure_types": failure_types_for_result_class(result_class),
        "materialized_candidates_csv": run_dir / "materialized_candidates.csv",
        "m267_preflight_summary_csv": run_dir / "m267_preflight_summary.csv",
        "training_started": False,
        "optimizer_started": False,
        "ppo_used": False,
        "promoted": False,
        "private_holdout_used": False,
        "next_blocker": (
            "replay-calibrated trust threshold redesign"
            if candidate_a_pass
            else "projection-line-search repair design or synthesis"
            if not any_candidate_pass
            else "branch trust metric ordering artifact audit"
        ),
        "summary_json": run_dir / "summary.json",
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run M267/M264 preflight for selected M1013 exact candidates.")
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--candidate", action="append", type=parse_candidate_spec, default=None)
    parser.add_argument("--corpus-csv", type=Path, default=DEFAULT_M267_CORPUS)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--max-continuation-steps", type=int, default=60)
    args = parser.parse_args()
    summary = run_m1013_exact_candidate_preflight(
        base_checkpoint=args.base_checkpoint,
        candidates=tuple(args.candidate) if args.candidate else DEFAULT_CANDIDATES,
        corpus_csv=args.corpus_csv,
        env_config_path=args.env_config,
        run_dir=args.run_dir,
        device=args.device,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"result_class={summary['result_class']}")
    print(f"preflight_pass_count={summary['preflight_pass_count']}")
    print(f"candidate_a_pass={summary['candidate_a_pass']}")
    print(f"summary={summary['summary_json']}")


if __name__ == "__main__":
    main()
