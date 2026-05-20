"""End-to-end M7 validation gate harness."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import pandas as pd

from autodrift.artifacts import make_run_dir, write_json


def run_command(name: str, command: list[str], log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{name}.log"
    with log_path.open("w", encoding="utf-8") as handle:
        handle.write(" ".join(command) + "\n\n")
        handle.flush()
        subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT, check=True)


def append_seed_csv(command: list[str], seed_csv: Path | None) -> list[str]:
    if seed_csv is None:
        return command
    return command + ["--seed-csv", str(seed_csv)]


def metric(frame: pd.DataFrame, policy: str, column: str) -> float:
    values = frame.loc[frame["policy"] == policy, column]
    if values.empty:
        return float("nan")
    return float(values.iloc[0])


def label_metric(frame: pd.DataFrame, policy: str, label: str, column: str) -> float:
    values = frame.loc[(frame["policy"] == policy) & (frame["obstacle_label"] == label), column]
    if values.empty:
        return float("nan")
    return float(values.iloc[0])


def probe_metric(frame: pd.DataFrame, target: str, feature_set: str, column: str) -> float:
    values = frame.loc[(frame["target"] == target) & (frame["feature_set"] == feature_set), column]
    if values.empty:
        return float("nan")
    return float(values.iloc[0])


def max_temporal_probe_lift(frame: pd.DataFrame) -> float:
    lifts = []
    for target in sorted(frame["target"].unique()):
        latent = probe_metric(frame, target, "latent", "test_accuracy")
        shuffled = probe_metric(frame, target, "shuffled_history_latent", "test_accuracy")
        if pd.notna(latent) and pd.notna(shuffled):
            lifts.append(latent - shuffled)
    return float(max(lifts)) if lifts else float("nan")


def compute_gate_summary(
    comparison: pd.DataFrame,
    ablation: pd.DataFrame,
    obstacle_labels: pd.DataFrame,
    m7a_probe: pd.DataFrame | None,
    m7b_probe: pd.DataFrame | None,
    min_success_delta: float,
    min_ablation_drop: float,
    max_aes_feasible_high_sideslip: float,
    min_probe_temporal_lift: float,
) -> dict:
    m5_success = metric(comparison, "m5", "success_rate")
    m7a_success = metric(comparison, "m7a", "success_rate")
    m7b_success = metric(comparison, "m7b", "success_rate")
    best_m7_success = max(m7a_success, m7b_success)

    m7a_ablation_drop = min(
        metric(ablation, "m7a", "success_rate") - metric(ablation, "m7a_noact", "success_rate"),
        metric(ablation, "m7a", "success_rate") - metric(ablation, "m7a_shuffle", "success_rate"),
    )
    m7b_ablation_drop = min(
        metric(ablation, "m7b", "success_rate") - metric(ablation, "m7b_noact", "success_rate"),
        metric(ablation, "m7b", "success_rate") - metric(ablation, "m7b_shuffle", "success_rate"),
    )
    best_ablation_drop = max(m7a_ablation_drop, m7b_ablation_drop)

    m7a_aes_sideslip = label_metric(obstacle_labels, "m7a", "aes_feasible", "high_sideslip_fraction_mean")
    m7b_aes_sideslip = label_metric(obstacle_labels, "m7b", "aes_feasible", "high_sideslip_fraction_mean")
    best_aes_sideslip = min(m7a_aes_sideslip, m7b_aes_sideslip)

    probe_lifts = []
    if m7a_probe is not None:
        probe_lifts.append(max_temporal_probe_lift(m7a_probe))
    if m7b_probe is not None:
        probe_lifts.append(max_temporal_probe_lift(m7b_probe))
    best_probe_lift = max(probe_lifts) if probe_lifts else float("nan")

    checks = {
        "success_beats_m5": best_m7_success >= m5_success + min_success_delta,
        "ablation_drop_present": best_ablation_drop >= min_ablation_drop,
        "aes_feasible_sideslip_ok": best_aes_sideslip <= max_aes_feasible_high_sideslip,
        "probe_temporal_lift_present": best_probe_lift >= min_probe_temporal_lift if probe_lifts else False,
    }
    return {
        "status": "passed" if all(checks.values()) else "needs_iteration",
        "checks": checks,
        "metrics": {
            "m5_success_rate": m5_success,
            "m7a_success_rate": m7a_success,
            "m7b_success_rate": m7b_success,
            "best_m7_success_delta_vs_m5": best_m7_success - m5_success,
            "m7a_min_ablation_drop": m7a_ablation_drop,
            "m7b_min_ablation_drop": m7b_ablation_drop,
            "best_ablation_drop": best_ablation_drop,
            "m7a_aes_feasible_high_sideslip": m7a_aes_sideslip,
            "m7b_aes_feasible_high_sideslip": m7b_aes_sideslip,
            "best_probe_temporal_lift": best_probe_lift,
        },
        "thresholds": {
            "min_success_delta": min_success_delta,
            "min_ablation_drop": min_ablation_drop,
            "max_aes_feasible_high_sideslip": max_aes_feasible_high_sideslip,
            "min_probe_temporal_lift": min_probe_temporal_lift,
        },
    }


def markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    subset = frame[columns].copy()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = [header, separator]
    for _, row in subset.iterrows():
        values = []
        for column in columns:
            value = row[column]
            if isinstance(value, float):
                values.append(f"{value:.3f}")
            else:
                values.append(str(value))
        rows.append("| " + " | ".join(values) + " |")
    return "\n".join(rows)


def write_gate_report(
    path: Path,
    summary: dict,
    comparison: pd.DataFrame,
    ablation: pd.DataFrame,
    obstacle_labels: pd.DataFrame,
    m7a_probe: pd.DataFrame | None,
    m7b_probe: pd.DataFrame | None,
) -> None:
    lines = [
        "# M7 Gate Report",
        "",
        f"Status: `{summary['status']}`",
        "",
        "## Checks",
        "",
    ]
    for name, passed in summary["checks"].items():
        lines.append(f"- `{name}`: `{passed}`")
    lines.extend(
        [
            "",
            "## Key Metrics",
            "",
        ]
    )
    for name, value in summary["metrics"].items():
        lines.append(f"- `{name}`: `{value:.6f}`")
    lines.extend(
        [
            "",
            "## Policy Summary",
            "",
            markdown_table(
                comparison,
                ["policy", "success_rate", "collision_rate", "high_sideslip_fraction_mean", "plan_horizon_mean"],
            ),
            "",
            "## History Ablation Summary",
            "",
            markdown_table(
                ablation,
                ["policy", "success_rate", "collision_rate", "high_sideslip_fraction_mean", "plan_horizon_mean"],
            ),
            "",
            "## Obstacle Label Summary",
            "",
            markdown_table(
                obstacle_labels,
                ["policy", "obstacle_label", "episodes", "success_rate", "high_sideslip_fraction_mean"],
            ),
        ]
    )
    if m7a_probe is not None:
        lines.extend(
            [
                "",
                "## M7-A Probe Summary",
                "",
                markdown_table(m7a_probe, ["target", "feature_set", "test_accuracy", "majority_accuracy", "accuracy_lift"]),
            ]
        )
    if m7b_probe is not None:
        lines.extend(
            [
                "",
                "## M7-B Probe Summary",
                "",
                markdown_table(m7b_probe, ["target", "feature_set", "test_accuracy", "majority_accuracy", "accuracy_lift"]),
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AutoDrift M7 validation gate.")
    parser.add_argument("--env-config", type=Path, default=Path("configs/m7_obstacle_aes_weighted_holdout_eval.json"))
    parser.add_argument("--m5-checkpoint", type=Path, default=Path("runs/ppo_m5_obstacle_seed83/checkpoint.pt"))
    parser.add_argument("--m7a-checkpoint", type=Path, default=Path("runs/ppo_m7a_history_seed127/checkpoint.pt"))
    parser.add_argument("--m7b-checkpoint", type=Path, default=Path("runs/ppo_m7b_sequence_seed131/checkpoint.pt"))
    parser.add_argument("--episodes", type=int, default=100)
    parser.add_argument("--seed", type=int, default=900)
    parser.add_argument("--seed-csv", type=Path, default=None)
    parser.add_argument("--probe-episodes", type=int, default=100)
    parser.add_argument("--probe-seed", type=int, default=1200)
    parser.add_argument("--probe-epochs", type=int, default=160)
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="cpu")
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--skip-probes", action="store_true")
    parser.add_argument("--min-success-delta", type=float, default=0.01)
    parser.add_argument("--min-ablation-drop", type=float, default=0.02)
    parser.add_argument("--max-aes-feasible-high-sideslip", type=float, default=0.15)
    parser.add_argument("--min-probe-temporal-lift", type=float, default=0.02)
    args = parser.parse_args()

    run_dir = args.run_dir or make_run_dir(prefix="m7_gate", seed=args.seed)
    run_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = run_dir / "logs"
    python = sys.executable

    comparison_dir = run_dir / "benchmark_comparison"
    ablation_dir = run_dir / "history_ablation"
    run_command(
        "benchmark_comparison",
        append_seed_csv(
            [
                python,
                "-m",
                "autodrift.benchmark",
                "--episodes",
                str(args.episodes),
                "--seed",
                str(args.seed),
                "--policies",
                "aeb",
                "aes_heuristic",
                "envelope_aes",
                "--checkpoint-policy",
                f"m5={args.m5_checkpoint}",
                "--checkpoint-policy",
                f"m7a={args.m7a_checkpoint}",
                "--checkpoint-policy",
                f"m7b={args.m7b_checkpoint}",
                "--env-config",
                str(args.env_config),
                "--device",
                args.device,
                "--run-dir",
                str(comparison_dir),
            ],
            args.seed_csv,
        ),
        logs_dir,
    )
    run_command(
        "history_ablation",
        append_seed_csv(
            [
                python,
                "-m",
                "autodrift.benchmark",
                "--episodes",
                str(args.episodes),
                "--seed",
                str(args.seed),
                "--policies",
                "envelope_aes",
                "--checkpoint-policy",
                f"m5={args.m5_checkpoint}",
                "--checkpoint-policy",
                f"m7a={args.m7a_checkpoint}",
                "--checkpoint-policy",
                f"m7a_noact={args.m7a_checkpoint}@zero_action_history",
                "--checkpoint-policy",
                f"m7a_single={args.m7a_checkpoint}@single_frame_history",
                "--checkpoint-policy",
                f"m7a_shuffle={args.m7a_checkpoint}@shuffled_history",
                "--checkpoint-policy",
                f"m7b={args.m7b_checkpoint}",
                "--checkpoint-policy",
                f"m7b_noact={args.m7b_checkpoint}@zero_action_history",
                "--checkpoint-policy",
                f"m7b_shuffle={args.m7b_checkpoint}@shuffled_history",
                "--env-config",
                str(args.env_config),
                "--device",
                args.device,
                "--run-dir",
                str(ablation_dir),
            ],
            args.seed_csv,
        ),
        logs_dir,
    )

    m7a_probe = None
    m7b_probe = None
    if not args.skip_probes:
        for label, checkpoint in [("m7a", args.m7a_checkpoint), ("m7b", args.m7b_checkpoint)]:
            probe_dir = run_dir / f"latent_probe_{label}"
            run_command(
                f"latent_probe_{label}",
                [
                    python,
                    "-m",
                    "autodrift.latent_probe",
                    "--checkpoint",
                    str(checkpoint),
                    "--env-config",
                    str(args.env_config),
                    "--episodes",
                    str(args.probe_episodes),
                    "--seed",
                    str(args.probe_seed),
                    "--device",
                    args.device,
                    "--epochs",
                    str(args.probe_epochs),
                    "--run-dir",
                    str(probe_dir),
                ],
                logs_dir,
            )
        m7a_probe = pd.read_csv(run_dir / "latent_probe_m7a" / "probe_summary.csv")
        m7b_probe = pd.read_csv(run_dir / "latent_probe_m7b" / "probe_summary.csv")

    comparison = pd.read_csv(comparison_dir / "policy_summary.csv")
    ablation = pd.read_csv(ablation_dir / "policy_summary.csv")
    obstacle_labels = pd.read_csv(comparison_dir / "obstacle_label_summary.csv")
    summary = compute_gate_summary(
        comparison=comparison,
        ablation=ablation,
        obstacle_labels=obstacle_labels,
        m7a_probe=m7a_probe,
        m7b_probe=m7b_probe,
        min_success_delta=args.min_success_delta,
        min_ablation_drop=args.min_ablation_drop,
        max_aes_feasible_high_sideslip=args.max_aes_feasible_high_sideslip,
        min_probe_temporal_lift=args.min_probe_temporal_lift,
    )
    summary_json = run_dir / "summary.json"
    report_md = run_dir / "gate_summary.md"
    manifest_json = run_dir / "manifest.json"
    write_json(summary_json, summary)
    write_gate_report(report_md, summary, comparison, ablation, obstacle_labels, m7a_probe, m7b_probe)
    write_json(
        manifest_json,
        {
            "run_type": "m7_gate",
            "summary": summary,
            "seed_csv": args.seed_csv,
            "artifacts": {
                "comparison_dir": comparison_dir,
                "history_ablation_dir": ablation_dir,
                "summary_json": summary_json,
                "gate_summary_md": report_md,
                "logs_dir": logs_dir,
            },
        },
    )
    print(pd.DataFrame([{"status": summary["status"], **summary["metrics"]}]).to_string(index=False))
    print(f"run_dir={run_dir}")


if __name__ == "__main__":
    main()
