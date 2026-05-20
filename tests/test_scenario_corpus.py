import pandas as pd

from autodrift.scenario_corpus import label_counts, select_label_balanced_rows, write_corpus


def test_select_label_balanced_rows_stops_when_quotas_met():
    rows = [
        {"seed": 1, "obstacle_label": "aes_feasible"},
        {"seed": 2, "obstacle_label": "aes_feasible"},
        {"seed": 3, "obstacle_label": "drift_required"},
        {"seed": 4, "obstacle_label": "unavoidable"},
        {"seed": 5, "obstacle_label": "drift_required"},
    ]

    selected = select_label_balanced_rows(rows, per_label=1, labels=("aes_feasible", "drift_required"))

    assert [row["seed"] for row in selected] == [1, 3]
    assert label_counts(selected) == {"aes_feasible": 1, "drift_required": 1}


def test_write_corpus_outputs_label_and_vehicle_summaries(tmp_path):
    rows = [
        {
            "seed": 1,
            "terminated": False,
            "obstacle_label": "aes_feasible",
            "mu": 0.40,
            "mass_scale": 0.90,
            "cg_shift": -0.05,
            "brake_scale": 0.80,
            "tire_stiffness_scale": 0.75,
            "steer_tau_scale": 1.30,
        },
        {
            "seed": 2,
            "terminated": False,
            "obstacle_label": "drift_required",
            "mu": 0.60,
            "mass_scale": 1.10,
            "cg_shift": 0.05,
            "brake_scale": 1.10,
            "tire_stiffness_scale": 1.20,
            "steer_tau_scale": 0.80,
        },
    ]

    summary = write_corpus(tmp_path, rows, candidates=10, labels=("aes_feasible", "drift_required"))

    assert summary["selected"] == 2
    assert summary["complete"]
    label_summary = pd.read_csv(tmp_path / "label_summary.csv")
    assert set(label_summary["obstacle_label"]) == {"aes_feasible", "drift_required"}
    assert (tmp_path / "vehicle_road_summary.csv").exists()
