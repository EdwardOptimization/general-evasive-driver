from autodrift.artifacts import read_json
from autodrift.engineering_controller_route_c_hf3_chrono_source_availability_preflight import (
    write_preflight_artifacts,
)


def test_missing_source_is_claim_safe_and_does_not_create_external_dir(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    design = repo_root / "docs" / "m2880.md"
    design.parent.mkdir()
    design.write_text("Chrono 10.0.0 source design", encoding="utf-8")
    source_root = tmp_path / "hf_backends" / "chrono" / "10.0.0" / "source"
    output_dir = repo_root / "runs" / "m2881"
    follow_up = repo_root / "experiments" / "manifests" / "m2882.json"

    summary = write_preflight_artifacts(
        m2880_design=design,
        source_root=source_root,
        expected_tag="10.0.0",
        expected_commit_prefix="9faf13d",
        output_dir=output_dir,
        follow_up_manifest=follow_up,
        repo_root=repo_root,
    )

    assert summary["status_pass"] is True
    assert summary["outcome"] == "source_unavailable_claim_safe"
    assert summary["source_available"] is False
    assert summary["source_root_exists"] is False
    assert not source_root.parent.exists()
    assert follow_up.exists()
    assert (output_dir / "source_availability_rows.csv").exists()
    assert read_json(output_dir / "summary.json")["outcome"] == "source_unavailable_claim_safe"


def test_source_with_cmake_lists_outside_repo_is_available_without_git_metadata(tmp_path):
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    design = repo_root / "docs" / "m2880.md"
    design.parent.mkdir()
    design.write_text("Chrono 10.0.0 source design", encoding="utf-8")
    source_root = tmp_path / "hf_backends" / "chrono" / "10.0.0" / "source"
    source_root.mkdir(parents=True)
    (source_root / "CMakeLists.txt").write_text("cmake_minimum_required(VERSION 3.16)\n", encoding="utf-8")
    output_dir = repo_root / "runs" / "m2881"
    follow_up = repo_root / "experiments" / "manifests" / "m2882.json"

    summary = write_preflight_artifacts(
        m2880_design=design,
        source_root=source_root,
        expected_tag="10.0.0",
        expected_commit_prefix="9faf13d",
        output_dir=output_dir,
        follow_up_manifest=follow_up,
        repo_root=repo_root,
    )

    assert summary["status_pass"] is True
    assert summary["outcome"] == "source_available_claim_safe"
    assert summary["source_available"] is True
    assert summary["source_root_exists"] is True
    assert summary["cmake_lists_exists"] is True
    assert summary["git_metadata_exists"] is False
    assert follow_up.exists()
