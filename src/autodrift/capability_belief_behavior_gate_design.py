"""M154 formal gate specification for capability-belief behavior admission."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import make_run_dir, write_csv_rows, write_json


DEFAULT_BASELINE_CHECKPOINT = "runs/m142_interpolate_m132_to_m139_s20/checkpoints/alpha_0_4.pt"
DEFAULT_ENV_CONFIG = "configs/m121_human_view_zero_obstacle_relvel.json"
DEFAULT_M118_PAIRS = "runs/m118_source_diverse_matched_current_seed9510/matched_pairs.csv"
DEFAULT_M133_REFERENCE_MANIFEST = "runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json"
DEFAULT_M133_CASES = (
    "runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv",
    "runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv",
)
PROTECTED_CRITICAL_KEY = "9944|perturbed|28|28"
REQUIRED_INTERVENTIONS = (
    "reset_recurrent_state",
    "zero_current_response",
    "zero_all_response",
    "zero_action_history",
    "wrong_matched_history",
    "delayed_history",
)


def _candidate_policy_args(candidate_name: str, candidate_checkpoint: str) -> list[str]:
    return [
        f"--checkpoint-policy {candidate_name}={candidate_checkpoint}",
        f"--checkpoint-policy {candidate_name}_reset={candidate_checkpoint}@reset_recurrent_state",
        f"--checkpoint-policy {candidate_name}_zero_current={candidate_checkpoint}@zero_current_response",
        f"--checkpoint-policy {candidate_name}_zero_all={candidate_checkpoint}@zero_all_response",
        f"--checkpoint-policy {candidate_name}_noact={candidate_checkpoint}@zero_action_history",
    ]


def behavior_benchmark_command(
    *,
    candidate_name: str,
    candidate_checkpoint: str,
    baseline_checkpoint: str,
    env_config: str,
    seed: int,
    episodes: int,
    run_dir: str,
) -> str:
    policy_args = [
        f"--checkpoint-policy m142_a400={baseline_checkpoint}",
        *_candidate_policy_args(candidate_name, candidate_checkpoint),
    ]
    return " ".join(
        [
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.benchmark",
            f"--env-config {env_config}",
            f"--episodes {episodes}",
            f"--seed {seed}",
            "--policies heuristic",
            *policy_args,
            "--device cpu",
            f"--run-dir {run_dir}",
        ]
    )


def critical_key_command(
    *,
    candidate_name: str,
    candidate_checkpoint: str,
    baseline_checkpoint: str,
    reference_manifest: str,
    reference_cases: tuple[str, ...],
    run_dir: str,
) -> str:
    case_args = [f"--reference-cases-csv {path}" for path in reference_cases]
    return " ".join(
        [
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.critical_key_replay_guard",
            f"--reference-manifest {reference_manifest}",
            *case_args,
            f"--case-key '{PROTECTED_CRITICAL_KEY}'",
            f"--checkpoint-policy m142_a400={baseline_checkpoint}",
            f"--checkpoint-policy {candidate_name}={candidate_checkpoint}",
            "--reference-policy m142_a400",
            "--device cpu",
            f"--run-dir {run_dir}",
        ]
    )


def action_intervention_command(
    *,
    candidate_name: str,
    candidate_checkpoint: str,
    env_config: str,
    pairs_csv: str,
    run_dir: str,
) -> str:
    return " ".join(
        [
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_intervention_gate",
            f"--checkpoint-policy {candidate_name}={candidate_checkpoint}",
            f"--env-config {env_config}",
            f"--pairs-csv {pairs_csv}",
            "--delay-steps 10",
            "--min-action-distance 0.02",
            "--max-pairs-per-checkpoint-target 80",
            "--device cpu",
            f"--run-dir {run_dir}",
        ]
    )


def outcome_intervention_command(
    *,
    candidate_name: str,
    candidate_checkpoint: str,
    env_config: str,
    pairs_csv: str,
    run_dir: str,
) -> str:
    return " ".join(
        [
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.matched_history_outcome_gate",
            f"--checkpoint-policy {candidate_name}={candidate_checkpoint}",
            f"--env-config {env_config}",
            f"--pairs-csv {pairs_csv}",
            "--delay-steps 10",
            "--min-action-distance 0.02",
            "--max-pairs-per-checkpoint-target 80",
            "--max-continuation-steps 40",
            "--device cpu",
            f"--run-dir {run_dir}",
        ]
    )


def strict_surface_command(
    *,
    candidate_checkpoint: str,
    env_config: str,
    seed: int,
    run_dir: str,
) -> str:
    return " ".join(
        [
            "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.snapshot_bank_relocation",
            f"--env-config {env_config}",
            f"--checkpoint {candidate_checkpoint}",
            "--episodes 60",
            f"--seed {seed}",
            "--device cpu",
            "--nominal-friction-mu-range 0.85,1.15",
            "--perturbed-friction-mu-range 0.25,0.35",
            "--obstacle-perception-reveal-step 20",
            "--obstacle-perception-reveal-distance 16",
            "--bank-obstacle-distance-range 5,12",
            "--bank-stride-steps 3",
            "--bank-max-snapshots 30",
            "--bank-max-pairs-per-seed 3",
            "--snapshot-relocation-distances 10,11,12",
            "--snapshot-relocation-lateral-offsets=-1",
            "--snapshot-relocation-half-widths 0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4",
            "--max-visible-distance 0.75",
            "--max-response-distance 0.35",
            "--max-context-distance 0.05",
            "--min-margin-gap 0.005",
            "--max-normal-margin 0.20",
            "--max-continuation-steps 40",
            "--probe-strategy steer_brake",
            "--probe-steer-amplitude 0.25",
            "--probe-brake-level 0.20",
            "--probe-period-steps 20",
            "--top-k 200",
            "--max-selected-per-physical-pair 1",
            "--max-selected-per-seed 2",
            "--outcome-export-min-margin-gap 0.005",
            "--export-only-accepted-outcomes",
            f"--run-dir {run_dir}",
        ]
    )


def build_gate_spec(
    *,
    candidate_name: str,
    candidate_checkpoint: str,
    baseline_checkpoint: str = DEFAULT_BASELINE_CHECKPOINT,
    env_config: str = DEFAULT_ENV_CONFIG,
    m118_pairs_csv: str = DEFAULT_M118_PAIRS,
    behavior_episodes: int = 80,
    behavior_seeds: tuple[int, ...] = (9503, 9504),
    strict_surface_seeds: tuple[int, ...] = (9900, 9920),
) -> dict[str, Any]:
    stages: list[dict[str, Any]] = [
        {
            "id": "actor_input_contract",
            "kind": "contract",
            "required": True,
            "pass_thresholds": {
                "actor_obs_dim": 72,
                "actor_encoder": "human_view_online_gru",
                "forbidden_actor_fields": [
                    "mu",
                    "mass",
                    "tire_stiffness",
                    "brake_scale",
                    "actuator_tau",
                    "oracle_feasibility",
                    "obstacle_label",
                    "speed_ref",
                    "beta_target",
                    "path_error",
                    "heading_error",
                    "TTC",
                    "required_clearance",
                ],
            },
            "reason": "No behavior result is admissible if the actor input contract changes or leaks oracle fields.",
        },
        {
            "id": "behavior_retention",
            "kind": "benchmark",
            "required": True,
            "commands": [
                behavior_benchmark_command(
                    candidate_name=candidate_name,
                    candidate_checkpoint=candidate_checkpoint,
                    baseline_checkpoint=baseline_checkpoint,
                    env_config=env_config,
                    seed=seed,
                    episodes=behavior_episodes,
                    run_dir=f"runs/m154_{candidate_name}_behavior_gate_seed{seed}",
                )
                for seed in behavior_seeds
            ],
            "pass_thresholds": {
                "normal_success_min": "baseline_success - 0.0125",
                "normal_clearance_margin_mean_min": "baseline_clearance_margin_mean - 0.02",
                "collision_rate_max": "baseline_collision_rate + 0.0125",
                "behavior_seed_count_min": len(behavior_seeds),
            },
            "reason": "Capability-belief training must not wash out the existing guarded behavior surface.",
        },
        {
            "id": "response_history_interventions",
            "kind": "benchmark_ablation",
            "required": True,
            "interventions": [
                "reset_recurrent_state",
                "zero_current_response",
                "zero_all_response",
                "zero_action_history",
            ],
            "pass_thresholds": {
                "zero_current_success_gap_min": 0.05,
                "zero_all_success_gap_min": 0.05,
                "reset_success_gap_min": 0.00,
                "zero_action_success_gap_min_for_ppo_admission": 0.00,
                "zero_action_success_gap_min_for_driver_claim": 0.05,
            },
            "reason": "The next PPO-ready candidate must retain causal dependence on sensed response history.",
        },
        {
            "id": "critical_key_replay",
            "kind": "critical_key_guard",
            "required": True,
            "commands": [
                critical_key_command(
                    candidate_name=candidate_name,
                    candidate_checkpoint=candidate_checkpoint,
                    baseline_checkpoint=baseline_checkpoint,
                    reference_manifest=DEFAULT_M133_REFERENCE_MANIFEST,
                    reference_cases=DEFAULT_M133_CASES,
                    run_dir=f"runs/m154_{candidate_name}_critical_key_guard_seed9944",
                )
            ],
            "pass_thresholds": {
                "protected_key": PROTECTED_CRITICAL_KEY,
                "accepted_cases_min": "1 / 1",
                "margin_gap_min": 0.005,
            },
            "reason": "M141 showed fixed losses can improve while a near-threshold rollout key disappears.",
        },
        {
            "id": "matched_history_action_gate",
            "kind": "wrong_history_action",
            "required": True,
            "commands": [
                action_intervention_command(
                    candidate_name=candidate_name,
                    candidate_checkpoint=candidate_checkpoint,
                    env_config=env_config,
                    pairs_csv=m118_pairs_csv,
                    run_dir=f"runs/m154_{candidate_name}_action_intervention_gate_seed9510",
                )
            ],
            "pass_thresholds": {
                "wrong_matched_history_physical_pairs_min": 100,
                "wrong_matched_history_above_threshold_fraction_min": 0.70,
                "wrong_matched_history_closer_to_right_fraction_min": 0.65,
            },
            "reason": "Action-level wrong-history dependence must survive on the source-diverse M118 corpus.",
        },
        {
            "id": "matched_history_outcome_gate",
            "kind": "wrong_history_outcome",
            "required": True,
            "commands": [
                outcome_intervention_command(
                    candidate_name=candidate_name,
                    candidate_checkpoint=candidate_checkpoint,
                    env_config=env_config,
                    pairs_csv=m118_pairs_csv,
                    run_dir=f"runs/m154_{candidate_name}_outcome_intervention_gate_seed9510",
                )
            ],
            "pass_thresholds": {
                "wrong_history_margin_gap_mean_min": 0.005,
                "wrong_history_success_drop_pairs_min": 6,
                "selected_physical_pairs_min": 6,
            },
            "reason": "Action differences are not enough; wrong history must hurt rollout outcome near the boundary.",
        },
        {
            "id": "strict_proof_surface",
            "kind": "snapshot_bank_relocation",
            "required": True,
            "commands": [
                strict_surface_command(
                    candidate_checkpoint=candidate_checkpoint,
                    env_config=env_config,
                    seed=seed,
                    run_dir=f"runs/m154_{candidate_name}_strict_60ep_seed{seed}",
                )
                for seed in strict_surface_seeds
            ],
            "pass_thresholds": {
                "seed_9900_selected_physical_pairs_min": 10,
                "seed_9900_selected_seeds_min": 8,
                "seed_9920_selected_physical_pairs_min": 9,
                "seed_9920_selected_seeds_min": 8,
                "m62_control_selected_physical_pairs_max": 0,
            },
            "reason": "A candidate must preserve the strict M133/M142 proof surface before PPO continuation.",
        },
        {
            "id": "promotion_boundary",
            "kind": "decision_boundary",
            "required": True,
            "pass_thresholds": {
                "ppo_admission": "all required stages pass",
                "driver_promotion": "not allowed by M154; needs full ideal driver gate later",
            },
            "reason": "Passing this gate admits only guarded PPO continuation, never full driver success.",
        },
    ]
    return {
        "run_type": "capability_belief_behavior_gate_design",
        "candidate_name": candidate_name,
        "candidate_checkpoint": candidate_checkpoint,
        "baseline_checkpoint": baseline_checkpoint,
        "env_config": env_config,
        "m118_pairs_csv": m118_pairs_csv,
        "required_interventions": list(REQUIRED_INTERVENTIONS),
        "gate_stage_count": len(stages),
        "stages": stages,
        "decision_rule": "admit guarded PPO only if all required stages pass; never promote driver from M154 alone",
    }


def gate_checklist_rows(spec: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for stage in spec["stages"]:
        rows.append(
            {
                "stage_id": stage["id"],
                "kind": stage["kind"],
                "required": bool(stage["required"]),
                "command_count": len(stage.get("commands", [])),
                "thresholds": "; ".join(f"{key}={value}" for key, value in stage["pass_thresholds"].items()),
                "reason": stage["reason"],
            }
        )
    return rows


def write_gate_design_artifacts(run_dir: Path, spec: dict[str, Any]) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    write_json(run_dir / "gate_spec.json", spec)
    write_csv_rows(run_dir / "gate_checklist.csv", gate_checklist_rows(spec))
    command_rows: list[dict[str, Any]] = []
    for stage in spec["stages"]:
        for index, command in enumerate(stage.get("commands", [])):
            command_rows.append({"stage_id": stage["id"], "command_index": index, "command": command})
    write_csv_rows(run_dir / "command_plan.csv", command_rows)
    write_json(
        run_dir / "summary.json",
        {
            "run_type": "capability_belief_behavior_gate_design",
            "candidate_name": spec["candidate_name"],
            "candidate_checkpoint": spec["candidate_checkpoint"],
            "gate_stage_count": spec["gate_stage_count"],
            "required_stage_count": sum(1 for stage in spec["stages"] if stage["required"]),
            "required_interventions": spec["required_interventions"],
            "decision_rule": spec["decision_rule"],
            "artifacts": {
                "gate_spec_json": run_dir / "gate_spec.json",
                "gate_checklist_csv": run_dir / "gate_checklist.csv",
                "command_plan_csv": run_dir / "command_plan.csv",
            },
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Write the M154 capability-belief behavior gate design.")
    parser.add_argument("--candidate-name", default="candidate")
    parser.add_argument("--candidate-checkpoint", default="<capability_belief_candidate_checkpoint.pt>")
    parser.add_argument("--baseline-checkpoint", default=DEFAULT_BASELINE_CHECKPOINT)
    parser.add_argument("--env-config", default=DEFAULT_ENV_CONFIG)
    parser.add_argument("--m118-pairs-csv", default=DEFAULT_M118_PAIRS)
    parser.add_argument("--behavior-episodes", type=int, default=80)
    parser.add_argument("--behavior-seeds", default="9503,9504")
    parser.add_argument("--strict-surface-seeds", default="9900,9920")
    parser.add_argument("--run-dir", type=Path, default=None)
    args = parser.parse_args()
    behavior_seeds = tuple(int(item.strip()) for item in args.behavior_seeds.split(",") if item.strip())
    strict_surface_seeds = tuple(int(item.strip()) for item in args.strict_surface_seeds.split(",") if item.strip())
    spec = build_gate_spec(
        candidate_name=args.candidate_name,
        candidate_checkpoint=args.candidate_checkpoint,
        baseline_checkpoint=args.baseline_checkpoint,
        env_config=args.env_config,
        m118_pairs_csv=args.m118_pairs_csv,
        behavior_episodes=args.behavior_episodes,
        behavior_seeds=behavior_seeds,
        strict_surface_seeds=strict_surface_seeds,
    )
    run_dir = args.run_dir or make_run_dir(prefix="m154_capability_belief_behavior_gate_design")
    write_gate_design_artifacts(run_dir, spec)
    print(f"wrote {spec['gate_stage_count']} gate stages to {run_dir}")


if __name__ == "__main__":
    main()
