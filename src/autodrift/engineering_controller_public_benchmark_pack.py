"""Materialize a claim-bounded public engineering benchmark pack."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_csv_rows, write_json


DEFAULT_PACK_ID = "engineering_controller_source_only_diagnostics_m2505"
DEFAULT_MILESTONE = "m2505-engineering-controller-public-benchmark-pack-materialization-preflight"
DEFAULT_NEXT_BLOCKER = "m2506-engineering-controller-public-benchmark-pack-result-audit"
REQUIRED_FILES = (
    "README.md",
    "artifact_manifest.csv",
    "claim_boundary.md",
    "actor_contract.md",
    "checkpoint_lineage.md",
    "scenario_role_diagnostics.md",
    "baseline_comparison_diagnostics.md",
    "known_limitations.md",
    "reproduce.md",
    "summary.json",
)
ARTIFACT_MANIFEST_FIELDNAMES = [
    "artifact_id",
    "path",
    "artifact_type",
    "source_milestone",
    "included_in_pack",
    "public_claim_scope",
    "forbidden_interpretation",
    "source_exists",
]
SOURCE_ARTIFACTS = (
    (
        "observation_contract",
        "docs/observation-contract.md",
        "contract",
        "m2504",
        "P0 72 observation and deployed 3-action boundary",
        "not a performance result",
    ),
    (
        "post_m2470_route_plan",
        "docs/post-m2470-route-plan.md",
        "route_plan",
        "post-m2470",
        "engineering route and public benchmark pack motivation",
        "not a milestone result",
    ),
    (
        "m2503_synthesis",
        "docs/m2503-engineering-controller-source-only-metric-panel-branch-synthesis.md",
        "synthesis",
        "m2503",
        "source-only metric branch synthesis and next-branch decision",
        "not driver performance",
    ),
    (
        "m2502_audit",
        "docs/m2502-engineering-controller-source-only-baseline-comparison-result-audit.md",
        "audit",
        "m2502",
        "diagnostic baseline comparison artifact audit",
        "not a controller ranking",
    ),
    (
        "m2501_result_doc",
        "docs/m2501-engineering-controller-source-only-baseline-comparison-implementation-preflight.md",
        "result_doc",
        "m2501",
        "source-only baseline comparison implementation preflight",
        "not a winner selection",
    ),
    (
        "m2501_summary",
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json",
        "summary_json",
        "m2501",
        "900-row source-only diagnostic comparison summary",
        "not a success-rate verdict",
    ),
    (
        "m2501_panel",
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/controller_role_metric_panel.csv",
        "csv",
        "m2501",
        "9-row role-subject diagnostic panel",
        "not a leaderboard",
    ),
    (
        "m2501_telemetry",
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/telemetry_rows.csv",
        "csv",
        "m2501",
        "900 diagnostic telemetry rows",
        "not outcome labels",
    ),
    (
        "m2500_design",
        "docs/m2500-engineering-controller-source-only-baseline-comparison-design.md",
        "design",
        "m2500",
        "baseline comparison protocol design",
        "not execution evidence",
    ),
    (
        "m2499_audit",
        "docs/m2499-engineering-controller-parameterized-source-only-role-metric-panel-result-audit.md",
        "audit",
        "m2499",
        "parameterized role metric panel audit",
        "not driver performance",
    ),
    (
        "m2498_result_doc",
        "docs/m2498-engineering-controller-parameterized-source-only-role-metric-panel-rerun.md",
        "result_doc",
        "m2498",
        "parameterized role metric panel rerun",
        "not high-fidelity validation",
    ),
    (
        "m2498_summary",
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json",
        "summary_json",
        "m2498",
        "300-row parameterized role metric summary",
        "not a success-rate result",
    ),
    (
        "m2498_panel",
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/role_metric_panel.csv",
        "csv",
        "m2498",
        "3-row role diagnostic panel",
        "not a controller ranking",
    ),
    (
        "m2498_telemetry",
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/telemetry_rows.csv",
        "csv",
        "m2498",
        "300 diagnostic telemetry rows",
        "not outcome labels",
    ),
)


@dataclass(frozen=True)
class PackResult:
    output_dir: Path
    summary: dict[str, Any]


def materialize_public_benchmark_pack(
    output_dir: Path,
    *,
    milestone: str = DEFAULT_MILESTONE,
    next_blocker: str = DEFAULT_NEXT_BLOCKER,
) -> PackResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    m2498_summary = read_json(
        "runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json"
    )
    m2501_summary = read_json(
        "runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json"
    )

    manifest_rows = _artifact_manifest_rows()
    write_csv_rows(
        output_dir / "artifact_manifest.csv",
        manifest_rows,
        fieldnames=ARTIFACT_MANIFEST_FIELDNAMES,
    )
    _write_pack_markdown(output_dir, m2498_summary=m2498_summary, m2501_summary=m2501_summary)

    summary = _summary(
        output_dir=output_dir,
        manifest_rows=manifest_rows,
        m2498_summary=m2498_summary,
        m2501_summary=m2501_summary,
        milestone=milestone,
        next_blocker=next_blocker,
    )
    write_json(output_dir / "summary.json", summary)
    return PackResult(output_dir=output_dir, summary=summary)


def _artifact_manifest_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path, artifact_type, milestone, scope, forbidden in SOURCE_ARTIFACTS:
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": path,
                "artifact_type": artifact_type,
                "source_milestone": milestone,
                "included_in_pack": True,
                "public_claim_scope": scope,
                "forbidden_interpretation": forbidden,
                "source_exists": Path(path).exists(),
            }
        )
    return rows


def _write_pack_markdown(
    output_dir: Path,
    *,
    m2498_summary: dict[str, Any],
    m2501_summary: dict[str, Any],
) -> None:
    (output_dir / "README.md").write_text(
        "\n".join(
            [
                "# Engineering Controller Source-Only Diagnostics Pack",
                "",
                "This pack is a source-only engineering diagnostic artifact. It documents",
                "the deployed actor I/O contract, checkpoint lineage, source-only role",
                "diagnostics, and source-only open-loop comparison diagnostics.",
                "",
                "It is not a driver-performance benchmark, controller leaderboard, high-fidelity",
                "validation result, paper result, finite-window-vs-GRU result, or level3",
                "self-identification proof.",
                "",
                "Primary source milestones: M2498, M2499, M2501, M2502, M2503, and M2504.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "claim_boundary.md").write_text(_claim_boundary_text(), encoding="utf-8")
    (output_dir / "actor_contract.md").write_text(_actor_contract_text(), encoding="utf-8")
    (output_dir / "checkpoint_lineage.md").write_text(_checkpoint_lineage_text(), encoding="utf-8")
    (output_dir / "scenario_role_diagnostics.md").write_text(
        _scenario_role_text(m2498_summary),
        encoding="utf-8",
    )
    (output_dir / "baseline_comparison_diagnostics.md").write_text(
        _baseline_comparison_text(m2501_summary),
        encoding="utf-8",
    )
    (output_dir / "known_limitations.md").write_text(_known_limitations_text(), encoding="utf-8")
    (output_dir / "reproduce.md").write_text(_reproduce_text(), encoding="utf-8")


def _claim_boundary_text() -> str:
    return """# Claim Boundary

Allowed claim:

```text
This pack provides source-only engineering diagnostic artifacts for a same-contract
recurrent actor and fixed open-loop action baselines.
```

Rejected claims:

```text
driver performance
success-rate benchmark
controller ranking
controller-family ranking
winner selection
checkpoint promotion
high-fidelity validation readiness
current-sim benchmark verdict
paper-level evidence
finite-window-vs-GRU conclusion
level3 self-identification
```

No success rate, ranking, winner, validation verdict, paper verdict, or
self-identification verdict is computed or claimed by this pack.
"""


def _actor_contract_text() -> str:
    return """# Actor Contract

P0 observation shape: 72

action shape: 3

actor encoder: `human_view_online_gru`

action sequence horizon: `1`

Action vector:

```text
[steering_command, throttle_command, brake_command]
```

Physical pedal mapping:

```text
physical_throttle = 0.5 * (throttle_command + 1)
physical_brake = 0.5 * (brake_command + 1)
```

Allowed actor-visible inputs:

```text
ego kinematics / IMU-like response
steering/throttle/brake actuator state
previous physical commands
ego-frame road/free-space geometry
ego-frame obstacle geometry and relative motion
online recurrent state from past command-response history
```

Forbidden actor-visible inputs:

```text
mu mass tire stiffness brake scale actuator tau slip tire force oracle
feasibility AEB/AES/drift labels controller mode speed_ref beta_target
path error heading error path curvature TTC required clearance oracle stopping
distance reward terms success labels
```
"""


def _checkpoint_lineage_text() -> str:
    return """# Checkpoint Lineage

Checkpoint:

```text
runs/m1154_row15_promoted_unsafe_margin_projection_probe/checkpoints/alpha_0_05.pt
```

Admission evidence:

```text
checkpoint_obs_dim: 72
checkpoint_action_dim: 3
checkpoint_actor_encoder: human_view_online_gru
checkpoint_action_sequence_horizon: 1
```

The checkpoint is admitted for engineering diagnostic panels only in this pack.
It is not promoted by this pack.
"""


def _scenario_role_text(summary: dict[str, Any]) -> str:
    return f"""# Scenario Role Diagnostics

Source:

```text
runs/m2498_engineering_controller_parameterized_source_only_role_metric_panel/summary.json
```

Key gates:

```text
result_class: {summary.get("result_class")}
status_pass: {str(summary.get("status_pass")).lower()}
parameterized_role_fixtures: {str(summary.get("parameterized_role_fixtures")).lower()}
telemetry rows / role panel rows: {summary.get("step_count")} / {summary.get("role_metric_panel_row_count")}
unique_role_reset_observation_digest_count: {summary.get("unique_role_reset_observation_digest_count")}
role_reset_observation_digests_differentiated: {str(summary.get("role_reset_observation_digests_differentiated")).lower()}
```

The role panel is diagnostic-only and does not compute success rate, ranking, or
driver-performance verdicts.
"""


def _baseline_comparison_text(summary: dict[str, Any]) -> str:
    return f"""# Baseline Comparison Diagnostics

Source:

```text
runs/m2501_engineering_controller_source_only_baseline_comparison_preflight/summary.json
```

Comparison subjects:

```text
m1154_policy_actor
coast_open_loop
straight_full_brake_open_loop
```

Key gates:

```text
result_class: {summary.get("result_class")}
status_pass: {str(summary.get("status_pass")).lower()}
telemetry rows / role-subject panel rows: {summary.get("telemetry_row_count")} / {summary.get("role_subject_panel_row_count")}
role_reset_digests_match_across_subjects: {str(summary.get("role_reset_digests_match_across_subjects")).lower()}
role_reset_digests_differentiated: {str(summary.get("role_reset_digests_differentiated")).lower()}
```

The comparison rows are diagnostic envelopes only. They do not rank controller
families or select a winner.
"""


def _known_limitations_text() -> str:
    return """# Known Limitations

- The execution artifacts are source-only HF0 diagnostics, not external
  high-fidelity simulation.
- The role fixtures are fixed and public.
- No success, collision, clearance, recovery-quality, or driver-performance
  verdict is computed.
- No controller-family ranking or winner selection is provided.
- No finite-window-vs-GRU or level3 self-identification test is included.
- No checkpoint is promoted by this pack.
"""


def _reproduce_text() -> str:
    return """# Reproduce

The pack materialization command is:

```text
PYTHONPATH=src python -m autodrift.engineering_controller_public_benchmark_pack --output-dir public_benchmark_packs/engineering_controller_source_only_diagnostics_m2505 --milestone m2505-engineering-controller-public-benchmark-pack-materialization-preflight --next-blocker m2506-engineering-controller-public-benchmark-pack-result-audit
```

The pack references committed artifacts rather than rerunning policy actions.
"""


def _summary(
    *,
    output_dir: Path,
    manifest_rows: list[dict[str, Any]],
    m2498_summary: dict[str, Any],
    m2501_summary: dict[str, Any],
    milestone: str,
    next_blocker: str,
) -> dict[str, Any]:
    required_file_paths = [output_dir / name for name in REQUIRED_FILES if name != "summary.json"]
    required_files_present = all(path.exists() for path in required_file_paths)
    source_artifacts_exist = all(bool(row["source_exists"]) for row in manifest_rows)
    missing_source_artifacts = [
        str(row["path"]) for row in manifest_rows if not bool(row["source_exists"])
    ]
    claim_boundary_text = (output_dir / "claim_boundary.md").read_text(encoding="utf-8")
    actor_contract_text = (output_dir / "actor_contract.md").read_text(encoding="utf-8")
    known_limitations_text = (output_dir / "known_limitations.md").read_text(encoding="utf-8")
    claim_boundary_rejects_forbidden = all(
        phrase in claim_boundary_text
        for phrase in [
            "driver performance",
            "success-rate benchmark",
            "controller ranking",
            "controller-family ranking",
            "winner selection",
            "high-fidelity validation",
            "paper-level evidence",
            "finite-window-vs-GRU conclusion",
            "level3 self-identification",
        ]
    )
    actor_contract_shape_72_action_3 = (
        "P0 observation shape: 72" in actor_contract_text
        and "action shape: 3" in actor_contract_text
    )
    known_limitations_present = "source-only HF0 diagnostics" in known_limitations_text
    source_only_diagnostic_scope = "source-only engineering diagnostic" in claim_boundary_text
    status_pass = (
        required_files_present
        and source_artifacts_exist
        and len(manifest_rows) >= 13
        and actor_contract_shape_72_action_3
        and claim_boundary_rejects_forbidden
        and known_limitations_present
        and source_only_diagnostic_scope
        and bool(m2498_summary.get("status_pass"))
        and bool(m2501_summary.get("status_pass"))
    )
    return {
        "result_class": (
            "engineering_controller_public_benchmark_pack_materialization_preflight_pass"
            if status_pass
            else "engineering_controller_public_benchmark_pack_materialization_preflight_failed"
        ),
        "status_pass": bool(status_pass),
        "pack_id": DEFAULT_PACK_ID,
        "pack_dir": str(output_dir),
        "milestone": str(milestone),
        "generated_at_utc": utc_timestamp(),
        "artifact_manifest": str(output_dir / "artifact_manifest.csv"),
        "artifact_manifest_rows": len(manifest_rows),
        "required_files": list(REQUIRED_FILES),
        "required_files_present": bool(required_files_present),
        "source_artifacts_exist": bool(source_artifacts_exist),
        "missing_source_artifacts": missing_source_artifacts,
        "actor_contract_shape_72_action_3": bool(actor_contract_shape_72_action_3),
        "claim_boundary_present": (output_dir / "claim_boundary.md").exists(),
        "claim_boundary_rejects_forbidden": bool(claim_boundary_rejects_forbidden),
        "known_limitations_present": bool(known_limitations_present),
        "source_only_diagnostic_scope": bool(source_only_diagnostic_scope),
        "m2498_status_pass": bool(m2498_summary.get("status_pass")),
        "m2501_status_pass": bool(m2501_summary.get("status_pass")),
        "external_high_fidelity_simulation_included": False,
        "policy_action_run": False,
        "policy_rollout_run": False,
        "measured_validation_run": False,
        "training_run": False,
        "replay_run": False,
        "ppo_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "checkpoint_promoted": False,
        "success_rate_computed": False,
        "controller_family_verdict_computed": False,
        "driver_performance_claim_made": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "next_blocker": str(next_blocker),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize public engineering benchmark pack.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--milestone", default=DEFAULT_MILESTONE)
    parser.add_argument("--next-blocker", default=DEFAULT_NEXT_BLOCKER)
    args = parser.parse_args()

    result = materialize_public_benchmark_pack(
        args.output_dir,
        milestone=args.milestone,
        next_blocker=args.next_blocker,
    )
    print(f"result_class={result.summary['result_class']}")
    print(f"status_pass={result.summary['status_pass']}")
    print(f"pack_dir={result.output_dir}")
    print(f"artifact_manifest_rows={result.summary['artifact_manifest_rows']}")
    print(f"summary={result.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
