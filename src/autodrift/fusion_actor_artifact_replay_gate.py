"""First public replay checks for the M1663 fusion_actor artifact."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from autodrift.artifacts import read_json, write_csv_rows, write_json
from autodrift.boundary_outcome_replay_gate import run_boundary_outcome_replay_gate
from autodrift.checkpoints import load_actor_critic_checkpoint
from autodrift.decisive_history_bounded_runner import assert_p0_model_contract
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec
from autodrift.public_base_controlled_fusion_candidate_replay_gate import DEFAULT_ENV_CONFIG


DEFAULT_CHECKPOINT = Path("runs/m1663_fusion_actor_checkpoint_artifact/checkpoints/alpha_0_2_fusion_actor_repaired.pt")
DEFAULT_ARTIFACT_SUMMARY = Path("runs/m1663_fusion_actor_checkpoint_artifact/summary.json")
DEFAULT_BASE_CHECKPOINT = Path("runs/m1362_bidirectional_active_set_interpolation_preflight/checkpoints/alpha_0_1.pt")
DEFAULT_RUN_DIR = Path("runs/m1666_fusion_actor_artifact_replay_first_check")
BASE_LABEL = "m1362_alpha_0_1"
CANDIDATE_LABEL = "m1663_alpha_0_2_repaired"
DEFAULT_MAX_CONTINUATION_STEPS = 60
FIRST_CHECK_SURFACES: tuple[tuple[str, Path], ...] = (
    ("m183_m170", Path("runs/m183_m170_boundary_outcome_corpus_dedup_seed9510/boundary_outcome_corpus.csv")),
    ("m267_m264", Path("runs/m267_m264_boundary_outcome_corpus_seed10070/boundary_outcome_corpus.csv")),
)

ReplayFunction = Callable[..., dict[str, Any]]
SanityFunction = Callable[..., dict[str, Any]]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_sanity(
    *,
    checkpoint: Path,
    artifact_summary: Path,
    device: str,
) -> dict[str, Any]:
    expected = read_json(artifact_summary)
    expected_sha = str(expected.get("artifact_sha256", ""))
    actual_sha = sha256_file(checkpoint) if checkpoint.exists() else ""
    load_error = ""
    contract_error = ""
    obs_dim = -1
    actor_encoder = ""
    try:
        model, loaded = load_actor_critic_checkpoint(checkpoint, device=device)
        obs_dim = int(getattr(model, "obs_dim", -1))
        actor_encoder = str(getattr(model, "actor_encoder", ""))
        assert_p0_model_contract(model)
        artifact_label = str((loaded.get("metadata") or {}).get("artifact_label", ""))
    except Exception as exc:  # pragma: no cover - exercised by integration runs.
        load_error = str(exc)
        artifact_label = ""
    if not load_error:
        try:
            model, _ = load_actor_critic_checkpoint(checkpoint, device=device)
            assert_p0_model_contract(model)
        except Exception as exc:  # pragma: no cover - defensive duplicate contract check.
            contract_error = str(exc)
    checksum_pass = bool(checkpoint.exists() and expected_sha and actual_sha == expected_sha)
    label_pass = artifact_label == "objective_sanity_artifact_only"
    contract_pass = bool(not load_error and not contract_error and obs_dim == 72)
    return {
        "checkpoint": str(checkpoint),
        "artifact_summary": str(artifact_summary),
        "checkpoint_exists": bool(checkpoint.exists()),
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "artifact_sha256_match": bool(checksum_pass),
        "artifact_label": artifact_label,
        "artifact_label_pass": bool(label_pass),
        "obs_dim": int(obs_dim),
        "actor_encoder": actor_encoder,
        "p0_actor_contract_pass": bool(contract_pass),
        "load_error": load_error,
        "contract_error": contract_error,
        "checkpoint_sanity_pass": bool(checksum_pass and label_pass and contract_pass),
    }


def _gate_row(label: str, corpus: Path, summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface": label,
        "corpus_csv": str(corpus),
        "run_dir": str(summary.get("run_dir", "")),
        "rows": int(summary.get("rows", 0)),
        "baseline_success_drop_count": int(summary.get("baseline_success_drop_count", 0)),
        "candidate_success_drop_count": int(summary.get("candidate_success_drop_count", 0)),
        "normal_success_delta": float(summary.get("normal_success_delta", 0.0)),
        "normal_margin_mean_delta": float(summary.get("normal_margin_mean_delta", 0.0)),
        "margin_gap_mean_delta": float(summary.get("margin_gap_mean_delta", 0.0)),
        "success_drop_count_delta": int(summary.get("success_drop_count_delta", 0)),
        "normal_success_retention_pass": bool(summary.get("normal_success_retention_pass", False)),
        "normal_margin_retention_pass": bool(summary.get("normal_margin_retention_pass", False)),
        "wrong_history_gap_retention_pass": bool(summary.get("wrong_history_gap_retention_pass", False)),
        "success_drop_count_retention_pass": bool(summary.get("success_drop_count_retention_pass", False)),
        "gate_pass": bool(summary.get("gate_pass", False)),
    }


def _failure_counts(rows: Sequence[Mapping[str, Any]], sanity: Mapping[str, Any]) -> dict[str, int]:
    contract_violation = 0 if bool(sanity.get("p0_actor_contract_pass", False)) else 1
    lineage_invalid = 0 if bool(sanity.get("artifact_sha256_match", False)) else 1
    metric_artifact = 0 if bool(sanity.get("checkpoint_sanity_pass", False)) else 1
    proof_washout = 0
    behavior_regression = 0
    for row in rows:
        if bool(row.get("gate_pass", False)):
            continue
        if not bool(row.get("wrong_history_gap_retention_pass", False)) or not bool(
            row.get("success_drop_count_retention_pass", False)
        ):
            proof_washout += 1
        if not bool(row.get("normal_success_retention_pass", False)) or not bool(
            row.get("normal_margin_retention_pass", False)
        ):
            behavior_regression += 1
    return {
        "proof_washout_count": int(proof_washout),
        "behavior_regression_count": int(behavior_regression),
        "lineage_invalid_count": int(lineage_invalid),
        "contract_violation_count": int(contract_violation),
        "metric_artifact_count": int(metric_artifact),
    }


def _guardrail_rows(summary: Mapping[str, Any]) -> list[dict[str, Any]]:
    keys = [
        "full_stack_replay_used_count",
        "ppo_used_count",
        "training_started_count",
        "promoted_count",
        "private_holdout_used_count",
        "actor_input_contract_changed_count",
        "level3_self_id_claim_count",
    ]
    return [{"guardrail": key, "violated": int(summary.get(key, 0)) != 0, "value": summary.get(key)} for key in keys]


def _result_class(summary: Mapping[str, Any]) -> str:
    if not bool(summary.get("checkpoint_sanity_pass", False)):
        return "fusion_actor_artifact_first_check_sanity_failure"
    if int(summary.get("replay_execution_error_count", 0)) != 0:
        return "fusion_actor_artifact_first_check_metric_artifact"
    if not bool(summary.get("m183_m170_first_check_pass", False)):
        return "fusion_actor_artifact_first_check_m183_m170_failure"
    if not bool(summary.get("m267_m264_first_check_pass", False)):
        return "fusion_actor_artifact_first_check_m267_m264_failure"
    if bool(summary.get("first_check_pass", False)):
        return "fusion_actor_artifact_first_check_public_pass"
    return "fusion_actor_artifact_first_check_public_failure"


def run_fusion_actor_artifact_replay_gate(
    *,
    checkpoint: Path | str,
    artifact_summary: Path | str,
    run_dir: Path | str,
    base_checkpoint: Path | str = DEFAULT_BASE_CHECKPOINT,
    env_config: Path | str = DEFAULT_ENV_CONFIG,
    mode: str = "first_check",
    device: str = "cpu",
    max_continuation_steps: int = DEFAULT_MAX_CONTINUATION_STEPS,
    replay_fn: ReplayFunction = run_boundary_outcome_replay_gate,
    sanity_fn: SanityFunction = checkpoint_sanity,
) -> dict[str, Any]:
    """Run checkpoint sanity plus first public proof replay checks."""

    if mode != "first_check":
        raise ValueError("only first_check mode is admitted for M1666")
    output = Path(run_dir)
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_path = Path(checkpoint)
    artifact_summary_path = Path(artifact_summary)
    base_path = Path(base_checkpoint)
    sanity = sanity_fn(checkpoint=checkpoint_path, artifact_summary=artifact_summary_path, device=device)
    write_json(output / "checkpoint_sanity.json", sanity)
    gate_rows: list[dict[str, Any]] = []
    replay_execution_error_count = 0
    if bool(sanity.get("checkpoint_sanity_pass", False)):
        for label, corpus in FIRST_CHECK_SURFACES:
            gate_dir = output / "replay" / label
            try:
                replay_summary = replay_fn(
                    checkpoint_specs=(
                        CheckpointSpec(label=BASE_LABEL, path=base_path),
                        CheckpointSpec(label=CANDIDATE_LABEL, path=checkpoint_path),
                    ),
                    corpus_csv=corpus,
                    env_config_path=Path(env_config),
                    max_rows=0,
                    max_continuation_steps=int(max_continuation_steps),
                    baseline_policy=BASE_LABEL,
                    candidate_policy=CANDIDATE_LABEL,
                    max_normal_success_drop=0.0,
                    max_normal_margin_regression=0.005,
                    max_margin_gap_regression=0.001,
                    max_success_drop_count_regression=0,
                    device=device,
                    run_dir=gate_dir,
                )
                replay_summary["run_dir"] = str(gate_dir)
                gate_rows.append(_gate_row(label, corpus, replay_summary))
            except Exception as exc:  # pragma: no cover - integration failure path.
                replay_execution_error_count += 1
                gate_rows.append(
                    {
                        "surface": label,
                        "corpus_csv": str(corpus),
                        "run_dir": str(gate_dir),
                        "rows": 0,
                        "gate_pass": False,
                        "execution_error": str(exc),
                    }
                )
    m183_pass = any(row["surface"] == "m183_m170" and bool(row.get("gate_pass", False)) for row in gate_rows)
    m267_pass = any(row["surface"] == "m267_m264" and bool(row.get("gate_pass", False)) for row in gate_rows)
    first_check_pass = bool(sanity.get("checkpoint_sanity_pass", False) and m183_pass and m267_pass and replay_execution_error_count == 0)
    failure_counts = _failure_counts(gate_rows, sanity)
    summary: dict[str, Any] = {
        "run_type": "fusion_actor_artifact_replay_gate",
        "mode": mode,
        "checkpoint": str(checkpoint_path),
        "artifact_summary": str(artifact_summary_path),
        "base_checkpoint": str(base_path),
        "env_config": str(env_config),
        "checkpoint_sanity_pass": bool(sanity.get("checkpoint_sanity_pass", False)),
        "artifact_sha256_match": bool(sanity.get("artifact_sha256_match", False)),
        "p0_actor_contract_pass": bool(sanity.get("p0_actor_contract_pass", False)),
        "m183_m170_first_check_pass": bool(m183_pass),
        "m267_m264_first_check_pass": bool(m267_pass),
        "first_check_pass": bool(first_check_pass),
        "replay_execution_error_count": int(replay_execution_error_count),
        **failure_counts,
        "full_stack_replay_used_count": 0,
        "ppo_used_count": 0,
        "training_started_count": 0,
        "promoted_count": 0,
        "private_holdout_used_count": 0,
        "actor_input_contract_changed_count": 0,
        "level3_self_id_claim_count": 0,
        "first_check_gate_summary_csv": output / "first_check_gate_summary.csv",
        "guardrail_summary_csv": output / "guardrail_summary.csv",
        "checkpoint_sanity_json": output / "checkpoint_sanity.json",
        "summary_json": output / "summary.json",
    }
    summary["passes_public_smoke_gates"] = bool(first_check_pass)
    summary["null_result_classification"] = _result_class(summary)
    summary["result_class"] = summary["null_result_classification"]
    write_csv_rows(output / "first_check_gate_summary.csv", gate_rows)
    write_csv_rows(output / "guardrail_summary.csv", _guardrail_rows(summary))
    write_json(output / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run first public replay checks for the fusion_actor artifact.")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--artifact-summary", type=Path, default=DEFAULT_ARTIFACT_SUMMARY)
    parser.add_argument("--base-checkpoint", type=Path, default=DEFAULT_BASE_CHECKPOINT)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--env-config", type=Path, default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--mode", choices=["first_check"], default="first_check")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--max-continuation-steps", type=int, default=DEFAULT_MAX_CONTINUATION_STEPS)
    args = parser.parse_args()
    summary = run_fusion_actor_artifact_replay_gate(
        checkpoint=args.checkpoint,
        artifact_summary=args.artifact_summary,
        base_checkpoint=args.base_checkpoint,
        run_dir=args.run_dir,
        env_config=args.env_config,
        mode=args.mode,
        device=args.device,
        max_continuation_steps=args.max_continuation_steps,
    )
    print(f"summary={summary['summary_json']}")
    print(f"checkpoint_sanity_pass={summary['checkpoint_sanity_pass']}")
    print(f"m183_m170_first_check_pass={summary['m183_m170_first_check_pass']}")
    print(f"m267_m264_first_check_pass={summary['m267_m264_first_check_pass']}")
    print(f"first_check_pass={summary['first_check_pass']}")
    print(f"null_result_classification={summary['null_result_classification']}")


if __name__ == "__main__":
    main()
