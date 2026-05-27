from pathlib import Path

import pytest

from autodrift.family_intersection_public_gate import (
    SourceCorpusSpec,
    classify_family_intersection_public_gate,
    failure_types_for_family_intersection_gate,
    parse_source_corpus_spec,
    validate_family_gate_specs,
)
from autodrift.hidden_envelope_multiseed_gate import CheckpointSpec


def _checkpoint(label: str, path: Path) -> CheckpointSpec:
    path.write_text("checkpoint", encoding="utf-8")
    return CheckpointSpec(label=label, path=path)


def _corpus(label: str, path: Path) -> SourceCorpusSpec:
    path.write_text("row_id,target\n", encoding="utf-8")
    return SourceCorpusSpec(label=label, corpus_csv=path)


def test_parse_source_corpus_spec_requires_label_and_path():
    spec = parse_source_corpus_spec("short61049=runs/corpus.csv")
    assert spec.label == "short61049"
    assert spec.corpus_csv == Path("runs/corpus.csv")

    with pytest.raises(ValueError, match="LABEL=PATH"):
        parse_source_corpus_spec("missing_equals")


def test_validate_family_gate_specs_requires_matching_source_and_corpus_labels(tmp_path):
    source = _checkpoint("short61049", tmp_path / "source.pt")
    candidate = _checkpoint("candidate", tmp_path / "candidate.pt")
    corpus = _corpus("short61050", tmp_path / "corpus.csv")

    with pytest.raises(ValueError, match="labels must match"):
        validate_family_gate_specs(
            source_policies=(source,),
            source_corpora=(corpus,),
            candidate_policy=candidate,
        )


def test_validate_family_gate_specs_rejects_candidate_label_collision(tmp_path):
    source = _checkpoint("short61049", tmp_path / "source.pt")
    candidate = _checkpoint("short61049", tmp_path / "candidate.pt")
    corpus = _corpus("short61049", tmp_path / "corpus.csv")

    with pytest.raises(ValueError, match="candidate policy label"):
        validate_family_gate_specs(
            source_policies=(source,),
            source_corpora=(corpus,),
            candidate_policy=candidate,
        )


def test_validate_family_gate_specs_accepts_matching_inputs(tmp_path):
    source = _checkpoint("short61049", tmp_path / "source.pt")
    candidate = _checkpoint("candidate", tmp_path / "candidate.pt")
    corpus = _corpus("short61049", tmp_path / "corpus.csv")

    sources, corpora = validate_family_gate_specs(
        source_policies=(source,),
        source_corpora=(corpus,),
        candidate_policy=candidate,
    )

    assert sources["short61049"].path == source.path
    assert corpora["short61049"].corpus_csv == corpus.corpus_csv


def test_classify_family_intersection_public_gate():
    assert (
        classify_family_intersection_public_gate(
            actor_inputs_changed=False,
            replay_gates_passed=3,
            replay_gate_count=3,
            training_started=False,
            ppo_used=False,
            promoted=False,
            private_holdout_used=False,
        )
        == "family_intersection_public_gate_pass"
    )
    assert (
        classify_family_intersection_public_gate(
            actor_inputs_changed=False,
            replay_gates_passed=2,
            replay_gate_count=3,
            training_started=False,
            ppo_used=False,
            promoted=False,
            private_holdout_used=False,
        )
        == "family_intersection_public_gate_proof_washout"
    )
    assert (
        classify_family_intersection_public_gate(
            actor_inputs_changed=True,
            replay_gates_passed=3,
            replay_gate_count=3,
            training_started=False,
            ppo_used=False,
            promoted=False,
            private_holdout_used=False,
        )
        == "family_intersection_public_gate_contract_artifact"
    )
    assert failure_types_for_family_intersection_gate("family_intersection_public_gate_proof_washout") == [
        "proof_washout"
    ]
