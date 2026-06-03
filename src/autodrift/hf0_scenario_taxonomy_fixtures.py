"""HF0 scenario taxonomy fixture catalog materialization."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from autodrift.artifacts import utc_timestamp, write_csv_rows, write_json
from autodrift.hf0_scenario_taxonomy_mapping import (
    ACTOR_VISIBLE_INPUTS,
    CURRENT_SIM_SURFACE_ID,
    FORBIDDEN_ACTOR_INPUT_TOKENS,
    ROLE_FAMILIES,
    SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID,
    SurfaceRoleRow,
    build_surface_role_rows,
)
from autodrift.high_fidelity_interface import ACTION_DIM, P0_OBSERVATION_DIM


ADMISSION_STATUSES = frozenset(
    {
        "baseline_reference",
        "diagnostic_reference_only",
        "admitted_for_materialization",
        "blocked",
    }
)

FIXTURE_METADATA_FIELDS = (
    "fixture_id",
    "fixture_admission_status",
    "scenario_role_label",
    "feasibility_class",
    "fixture_objective",
    "fixture_reason",
    "fixture_blocker",
)


@dataclass(frozen=True)
class FixtureCatalogRow:
    fixture_id: str
    surface_id: str
    role_family: str
    source_support_status: str
    fixture_admission_status: str
    actor_observation_shape: int
    action_shape: int
    actor_visible_inputs: tuple[str, ...]
    metadata_only_fields: tuple[str, ...]
    implementation_target: str
    blocker_if_not_admitted: str
    next_check: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "surface_id": self.surface_id,
            "role_family": self.role_family,
            "source_support_status": self.source_support_status,
            "fixture_admission_status": self.fixture_admission_status,
            "actor_observation_shape": self.actor_observation_shape,
            "action_shape": self.action_shape,
            "actor_visible_inputs": ";".join(self.actor_visible_inputs),
            "metadata_only_fields": ";".join(self.metadata_only_fields),
            "implementation_target": self.implementation_target,
            "blocker_if_not_admitted": self.blocker_if_not_admitted,
            "next_check": self.next_check,
        }


def build_fixture_catalog_rows() -> list[FixtureCatalogRow]:
    surface_rows = build_surface_role_rows()
    catalog_rows = [_fixture_row_from_surface_row(row) for row in surface_rows]
    validate_fixture_catalog_rows(catalog_rows)
    return catalog_rows


def validate_fixture_catalog_rows(rows: list[FixtureCatalogRow]) -> None:
    if not rows:
        raise ValueError("fixture catalog is empty")

    seen_by_surface: dict[str, set[str]] = {}
    for row in rows:
        if row.surface_id not in {CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID}:
            raise ValueError(f"unknown surface_id {row.surface_id}")
        if row.role_family not in ROLE_FAMILIES:
            raise ValueError(f"unknown role_family {row.role_family}")
        if row.fixture_admission_status not in ADMISSION_STATUSES:
            raise ValueError(f"unknown fixture_admission_status {row.fixture_admission_status}")
        if row.actor_observation_shape != P0_OBSERVATION_DIM:
            raise ValueError(
                f"{row.surface_id}/{row.role_family} changed observation shape to "
                f"{row.actor_observation_shape}"
            )
        if row.action_shape != ACTION_DIM:
            raise ValueError(f"{row.surface_id}/{row.role_family} changed action shape to {row.action_shape}")

        leaked = sorted(set(row.actor_visible_inputs).intersection(FORBIDDEN_ACTOR_INPUT_TOKENS))
        if leaked:
            raise ValueError(f"{row.surface_id}/{row.role_family} leaks metadata to actor inputs: {leaked}")
        for required in ("scenario_role_label", "feasibility_class", "fixture_admission_status"):
            if required not in row.metadata_only_fields:
                raise ValueError(f"{row.surface_id}/{row.role_family} missing metadata-only {required}")

        if row.source_support_status == "supported" and row.fixture_admission_status != "baseline_reference":
            raise ValueError(
                f"{row.surface_id}/{row.role_family} supported row must remain baseline_reference"
            )
        if row.source_support_status == "limited_fixture" and row.fixture_admission_status == "baseline_reference":
            raise ValueError(f"{row.surface_id}/{row.role_family} limited row was silently upgraded")
        if (
            row.surface_id == CURRENT_SIM_SURFACE_ID
            and row.source_support_status == "limited_fixture"
            and row.fixture_admission_status != "diagnostic_reference_only"
        ):
            raise ValueError(f"{row.surface_id}/{row.role_family} current-sim limited row escaped diagnostic reference")
        if (
            row.surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
            and row.source_support_status == "limited_fixture"
            and row.fixture_admission_status != "admitted_for_materialization"
        ):
            raise ValueError(f"{row.surface_id}/{row.role_family} source-only limited row was not admitted explicitly")

        seen_by_surface.setdefault(row.surface_id, set()).add(row.role_family)

    expected_roles = set(ROLE_FAMILIES)
    for surface_id in (CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID):
        missing = sorted(expected_roles - seen_by_surface.get(surface_id, set()))
        if missing:
            raise ValueError(f"{surface_id} missing fixture rows: {missing}")


def write_fixture_catalog(output_dir: Path) -> tuple[Path, list[FixtureCatalogRow]]:
    rows = build_fixture_catalog_rows()
    catalog_path = output_dir / "fixture_catalog.csv"
    write_csv_rows(
        catalog_path,
        [row.to_csv_row() for row in rows],
        fieldnames=[
            "fixture_id",
            "surface_id",
            "role_family",
            "source_support_status",
            "fixture_admission_status",
            "actor_observation_shape",
            "action_shape",
            "actor_visible_inputs",
            "metadata_only_fields",
            "implementation_target",
            "blocker_if_not_admitted",
            "next_check",
        ],
    )
    return catalog_path, rows


def run_fixture_materialization_preflight(output_dir: Path, *, next_blocker: str) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    catalog_path, rows = write_fixture_catalog(output_dir)
    surfaces = sorted({row.surface_id for row in rows})
    admission_counts = Counter(row.fixture_admission_status for row in rows)
    support_counts = Counter(row.source_support_status for row in rows)
    actor_metadata_leaks = _actor_metadata_leaks(rows)
    all_rows_preserve_observation_shape = all(row.actor_observation_shape == P0_OBSERVATION_DIM for row in rows)
    all_rows_preserve_action_shape = all(row.action_shape == ACTION_DIM for row in rows)
    scenario_labels_enter_actor_input = any("scenario_role_label" in row.actor_visible_inputs for row in rows)
    feasibility_classes_enter_actor_input = any("feasibility_class" in row.actor_visible_inputs for row in rows)
    hidden_values_enter_actor_input = any(actor_metadata_leaks.values())
    oracle_labels_enter_actor_input = any(
        token in actor_token
        for row in rows
        for actor_token in row.actor_visible_inputs
        for token in ("oracle", "unavoidable", "required_clearance", "ttc")
    )
    limited_rows_silently_upgraded = any(
        row.source_support_status == "limited_fixture" and row.fixture_admission_status == "baseline_reference"
        for row in rows
    )
    current_sim_limited_reference_count = sum(
        1
        for row in rows
        if row.surface_id == CURRENT_SIM_SURFACE_ID
        and row.source_support_status == "limited_fixture"
        and row.fixture_admission_status == "diagnostic_reference_only"
    )
    source_only_admitted_fixture_count = sum(
        1
        for row in rows
        if row.surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID
        and row.source_support_status == "limited_fixture"
        and row.fixture_admission_status == "admitted_for_materialization"
    )
    status_pass = (
        len(rows) == 10
        and surfaces == [CURRENT_SIM_SURFACE_ID, SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID]
        and set(ROLE_FAMILIES) == {row.role_family for row in rows}
        and all_rows_preserve_observation_shape
        and all_rows_preserve_action_shape
        and not scenario_labels_enter_actor_input
        and not feasibility_classes_enter_actor_input
        and not hidden_values_enter_actor_input
        and not oracle_labels_enter_actor_input
        and not limited_rows_silently_upgraded
        and current_sim_limited_reference_count == 2
        and source_only_admitted_fixture_count == 3
    )

    summary = {
        "milestone": "m2482-high-fidelity-interface-scenario-taxonomy-fixture-materialization-preflight",
        "generated_at_utc": utc_timestamp(),
        "result_class": "hf0_scenario_taxonomy_fixture_materialization_pass"
        if status_pass
        else "hf0_scenario_taxonomy_fixture_materialization_failed",
        "status_pass": bool(status_pass),
        "surface_count": len(surfaces),
        "surfaces": surfaces,
        "role_count": len(ROLE_FAMILIES),
        "roles": list(ROLE_FAMILIES),
        "catalog_row_count": len(rows),
        "source_support_status_counts": dict(sorted(support_counts.items())),
        "fixture_admission_status_counts": dict(sorted(admission_counts.items())),
        "actor_observation_shape": P0_OBSERVATION_DIM,
        "action_shape": ACTION_DIM,
        "all_rows_preserve_observation_shape": bool(all_rows_preserve_observation_shape),
        "all_rows_preserve_action_shape": bool(all_rows_preserve_action_shape),
        "scenario_labels_enter_actor_input": bool(scenario_labels_enter_actor_input),
        "feasibility_classes_enter_actor_input": bool(feasibility_classes_enter_actor_input),
        "hidden_values_enter_actor_input": bool(hidden_values_enter_actor_input),
        "oracle_labels_enter_actor_input": bool(oracle_labels_enter_actor_input),
        "limited_rows_silently_upgraded": bool(limited_rows_silently_upgraded),
        "current_sim_limited_reference_count": int(current_sim_limited_reference_count),
        "source_only_admitted_fixture_count": int(source_only_admitted_fixture_count),
        "actor_metadata_leaks": actor_metadata_leaks,
        "metadata_only_fields_checked": sorted({field for row in rows for field in row.metadata_only_fields}),
        "fixture_catalog": str(catalog_path),
        "external_high_fidelity_required": False,
        "external_high_fidelity_imported": False,
        "high_fidelity_simulation_run": False,
        "measured_validation_run": False,
        "policy_rollout_run": False,
        "training_run": False,
        "ranking_run": False,
        "winner_selected": False,
        "verdict_claim_made": False,
        "paper_claim_made": False,
        "finite_window_vs_gru_claim_made": False,
        "level3_self_id_claim_made": False,
        "current_sim_verdict_claim_made": False,
        "high_fidelity_validation_claim_made": False,
        "next_blocker": str(next_blocker),
    }
    write_json(output_dir / "summary.json", summary)
    return summary


def _fixture_row_from_surface_row(row: SurfaceRoleRow) -> FixtureCatalogRow:
    if row.support_status == "supported":
        return FixtureCatalogRow(
            fixture_id=f"hf0_{_surface_slug(row.surface_id)}_{row.role_family}_baseline",
            surface_id=row.surface_id,
            role_family=row.role_family,
            source_support_status=row.support_status,
            fixture_admission_status="baseline_reference",
            actor_observation_shape=row.actor_observation_shape,
            action_shape=row.action_shape,
            actor_visible_inputs=row.actor_visible_inputs,
            metadata_only_fields=_metadata_fields(row),
            implementation_target="baseline_fixture_reference",
            blocker_if_not_admitted="",
            next_check="keep baseline reference in catalog completeness checks",
        )

    limited_rows = {
        (CURRENT_SIM_SURFACE_ID, "stable_aes"): (
            "hf0_current_sim_stable_aes_reference",
            "diagnostic_reference_only",
            "current_sim_diagnostic_reference",
            "stable-AES reset-ready support remains partial; do not restart static current-sim repair without synthesis",
            "keep as reference metadata, not as pilot admission",
        ),
        (CURRENT_SIM_SURFACE_ID, "unavoidable_mitigation"): (
            "hf0_current_sim_unavoidable_mitigation_reference",
            "diagnostic_reference_only",
            "current_sim_diagnostic_reference",
            "unavoidable feasibility is oracle metadata and cannot become actor input",
            "define mitigation metrics only after fixture catalog materializes",
        ),
        (SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID, "stable_aes"): (
            "hf0_four_wheel_stable_aes_fixture",
            "admitted_for_materialization",
            "source_only_four_wheel_fixture_metadata",
            "",
            "materialize deterministic evasive-steering fixture metadata",
        ),
        (SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID, "drift_required_recovery"): (
            "hf0_four_wheel_drift_required_recovery_fixture",
            "admitted_for_materialization",
            "source_only_four_wheel_fixture_metadata",
            "",
            "materialize recovery fixture metadata and backend reset options",
        ),
        (SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID, "unavoidable_mitigation"): (
            "hf0_four_wheel_unavoidable_mitigation_fixture",
            "admitted_for_materialization",
            "source_only_four_wheel_fixture_metadata",
            "",
            "materialize mitigation fixture metadata with actor contract checks",
        ),
    }
    fixture_id, admission_status, target, blocker, next_check = limited_rows.get(
        (row.surface_id, row.role_family),
        (
            f"hf0_{_surface_slug(row.surface_id)}_{row.role_family}_blocked",
            "blocked",
            "blocked_until_design",
            "limited row has no M2481 fixture admission",
            "return to fixture design before materialization",
        ),
    )
    return FixtureCatalogRow(
        fixture_id=fixture_id,
        surface_id=row.surface_id,
        role_family=row.role_family,
        source_support_status=row.support_status,
        fixture_admission_status=admission_status,
        actor_observation_shape=row.actor_observation_shape,
        action_shape=row.action_shape,
        actor_visible_inputs=ACTOR_VISIBLE_INPUTS,
        metadata_only_fields=_metadata_fields(row),
        implementation_target=target,
        blocker_if_not_admitted=blocker,
        next_check=next_check,
    )


def _metadata_fields(row: SurfaceRoleRow) -> tuple[str, ...]:
    return tuple(dict.fromkeys(row.metadata_only_fields + FIXTURE_METADATA_FIELDS))


def _surface_slug(surface_id: str) -> str:
    if surface_id == CURRENT_SIM_SURFACE_ID:
        return "current_sim"
    if surface_id == SOURCE_ONLY_FOUR_WHEEL_SURFACE_ID:
        return "four_wheel"
    return surface_id.replace("_hf0", "")


def _actor_metadata_leaks(rows: list[FixtureCatalogRow]) -> dict[str, list[str]]:
    leaks: dict[str, list[str]] = {}
    for row in rows:
        leaked_tokens = sorted(set(row.actor_visible_inputs).intersection(FORBIDDEN_ACTOR_INPUT_TOKENS))
        if leaked_tokens:
            leaks[f"{row.surface_id}:{row.role_family}"] = leaked_tokens
    return leaks


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialize HF0 scenario taxonomy fixture catalog.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_fixture_materialization_preflight(args.output_dir, next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"catalog_row_count={summary['catalog_row_count']}")
    print(f"fixture_catalog={summary['fixture_catalog']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
