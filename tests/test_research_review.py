from autodrift.research_review import build_review_payload, render_review_markdown


def test_build_review_payload_prefers_scoreboard_decision():
    manifest = {
        "id": "m227",
        "type": "gate",
        "gate_tier": "process",
        "hypothesis": "audit PPO retention",
        "success_criteria": ["classify failure"],
        "failure_criteria": ["run PPO before audit"],
        "public_gates": ["protected key"],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": ["do not promote broad behavior alone"],
        "failure_types": ["proof_washout"],
        "promotion_decision": "pending",
        "decision_rule": "manual review",
        "lineage": {
            "parent_checkpoint": ["runs/m224/checkpoint.pt"],
            "derived_from": ["m226"],
            "blocked_by": ["m226"],
        },
    }
    row = {"milestone": "m227", "decision": "reject", "reason": "protected key failed"}

    payload = build_review_payload(manifest, scoreboard_row=row, generated_at_utc="20260522T000000Z")

    assert payload["promotion_decision"] == "reject"
    assert payload["decision_reason"] == "protected key failed"
    assert payload["lineage"]["parent_checkpoint"] == ["runs/m224/checkpoint.pt"]
    assert payload["lineage"]["parent_dataset"] == []


def test_render_review_markdown_includes_governance_sections():
    payload = {
        "milestone": "m227",
        "generated_at_utc": "20260522T000000Z",
        "type": "gate",
        "gate_tier": "process",
        "hypothesis": "audit PPO retention",
        "lineage": {
            "parent_checkpoint": ["runs/m224/checkpoint.pt"],
            "parent_dataset": [],
            "parent_config": [],
            "parent_objective": [],
            "derived_from": ["m226"],
            "blocked_by": ["m226"],
            "supersedes": [],
            "invalidates": [],
        },
        "success_criteria": ["classify failure"],
        "failure_criteria": ["run PPO before audit"],
        "public_gates": ["protected key"],
        "private_holdout_policy": "not_used",
        "forbidden_shortcuts": ["do not promote broad behavior alone"],
        "failure_types": ["proof_washout"],
        "promotion_decision": "reject",
        "decision_reason": "protected key failed",
        "scoreboard": {},
        "next_blocker": "design snippet-level PPO anchor",
    }

    text = render_review_markdown(payload)

    assert "## Failure Taxonomy" in text
    assert "- proof_washout" in text
    assert "## Holdout Policy" in text
    assert "design snippet-level PPO anchor" in text
