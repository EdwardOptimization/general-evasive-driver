"""Generate structured research milestone reviews from manifests."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from autodrift.artifacts import read_json, utc_timestamp, write_json
from autodrift.research_schema import PROCESS_V2_LINEAGE_FIELDS
from autodrift.research_validate import load_scoreboard


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item)]
    return [str(value)]


def _find_scoreboard_row(scoreboard_path: Path, milestone: str) -> dict[str, str] | None:
    if not scoreboard_path.exists():
        return None
    for row in load_scoreboard(scoreboard_path):
        if row["milestone"] == milestone:
            return row
    return None


def build_review_payload(
    manifest: dict[str, Any],
    scoreboard_row: dict[str, str] | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a deterministic review payload for a milestone manifest."""

    lineage = manifest.get("lineage", {})
    if not isinstance(lineage, dict):
        lineage = {}
    normalized_lineage = {
        field: _as_list(lineage.get(field))
        for field in PROCESS_V2_LINEAGE_FIELDS
    }
    gates = manifest.get("public_gates", [])
    if not isinstance(gates, list):
        gates = []
    failure_types = manifest.get("failure_types", [])
    if not isinstance(failure_types, list):
        failure_types = []

    decision = str(manifest.get("promotion_decision", "manual_review"))
    reason = str(manifest.get("decision_rule", ""))
    if scoreboard_row:
        decision = scoreboard_row.get("decision") or decision
        reason = scoreboard_row.get("reason") or reason

    return {
        "milestone": manifest["id"],
        "generated_at_utc": generated_at_utc or utc_timestamp(),
        "type": manifest.get("type", ""),
        "gate_tier": manifest.get("gate_tier", "legacy"),
        "hypothesis": manifest.get("hypothesis", ""),
        "lineage": normalized_lineage,
        "success_criteria": manifest.get("success_criteria", []),
        "failure_criteria": manifest.get("failure_criteria", []),
        "public_gates": gates,
        "private_holdout_policy": manifest.get("private_holdout_policy", "legacy"),
        "forbidden_shortcuts": manifest.get("forbidden_shortcuts", []),
        "failure_types": failure_types,
        "promotion_decision": decision,
        "decision_reason": reason,
        "scoreboard": scoreboard_row or {},
        "next_blocker": manifest.get("next_blocker", ""),
    }


def _bullet_lines(values: list[Any]) -> list[str]:
    if not values:
        return ["- None recorded."]
    return [f"- {value}" for value in values]


def render_review_markdown(payload: dict[str, Any]) -> str:
    """Render a compact milestone review markdown document."""

    lineage = payload["lineage"]
    lines = [
        f"# {payload['milestone']} Research Review",
        "",
        "## Summary",
        "",
        f"- Generated at UTC: {payload['generated_at_utc']}",
        f"- Type: {payload['type']}",
        f"- Gate tier: {payload['gate_tier']}",
        f"- Promotion decision: {payload['promotion_decision']}",
        f"- Decision reason: {payload['decision_reason']}",
        "",
        "## Hypothesis",
        "",
        str(payload["hypothesis"]),
        "",
        "## Lineage",
        "",
    ]
    for field in PROCESS_V2_LINEAGE_FIELDS:
        values = ", ".join(lineage[field]) if lineage[field] else "None"
        lines.append(f"- {field}: {values}")
    lines.extend(
        [
            "",
            "## Success Criteria",
            "",
            *_bullet_lines(payload["success_criteria"]),
            "",
            "## Failure Criteria",
            "",
            *_bullet_lines(payload["failure_criteria"]),
            "",
            "## Evidence Gates",
            "",
            *_bullet_lines(payload["public_gates"]),
            "",
            "## Holdout Policy",
            "",
            f"- {payload['private_holdout_policy']}",
            "",
            "## Forbidden Shortcuts",
            "",
            *_bullet_lines(payload["forbidden_shortcuts"]),
            "",
            "## Failure Taxonomy",
            "",
            *_bullet_lines(payload["failure_types"]),
            "",
            "## Scoreboard",
            "",
        ]
    )
    scoreboard = payload["scoreboard"]
    if scoreboard:
        for key, value in scoreboard.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- No scoreboard row recorded.")
    lines.extend(["", "## Next Blocker", "", str(payload["next_blocker"] or "None recorded."), ""])
    return "\n".join(lines)


def write_research_review(
    manifest_path: Path | str,
    scoreboard_path: Path | str = "experiments/scoreboard.csv",
    output_path: Path | str | None = None,
    json_output_path: Path | str | None = None,
) -> tuple[Path, Path]:
    manifest = read_json(manifest_path)
    scoreboard = Path(scoreboard_path)
    row = _find_scoreboard_row(scoreboard, str(manifest["id"]))
    payload = build_review_payload(manifest, scoreboard_row=row)

    output = Path(output_path) if output_path is not None else Path("docs/reviews") / f"{manifest['id']}.md"
    json_output = (
        Path(json_output_path)
        if json_output_path is not None
        else Path("experiments/reviews") / f"{manifest['id']}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_review_markdown(payload), encoding="utf-8")
    write_json(json_output, payload)
    return output, json_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a structured AutoDrift research milestone review.")
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--scoreboard", type=Path, default=Path("experiments/scoreboard.csv"))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    md_path, json_path = write_research_review(
        manifest_path=args.manifest,
        scoreboard_path=args.scoreboard,
        output_path=args.out,
        json_output_path=args.json_out,
    )
    print(f"review={md_path}")
    print(f"review_json={json_path}")


if __name__ == "__main__":
    main()
