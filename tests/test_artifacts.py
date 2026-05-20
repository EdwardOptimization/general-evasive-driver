import numpy as np

from autodrift.artifacts import make_run_dir, read_json, write_json


def test_json_artifact_roundtrip(tmp_path):
    path = tmp_path / "metrics" / "summary.json"
    write_json(path, {"value": np.float64(1.5), "items": np.array([1, 2, 3])})

    assert read_json(path) == {"items": [1, 2, 3], "value": 1.5}


def test_make_run_dir_is_unique(tmp_path):
    first = make_run_dir(tmp_path, prefix="smoke", seed=3)
    second = make_run_dir(tmp_path, prefix="smoke", seed=3)

    assert first.exists()
    assert second.exists()
    assert first != second
