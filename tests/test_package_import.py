import os
from pathlib import Path
import subprocess
import sys


def test_package_import_does_not_eager_import_env():
    repo_root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    script = "\n".join(
        [
            "import sys",
            "import autodrift",
            "print('autodrift.env' in sys.modules)",
            "from autodrift import AutoDriftEnv",
            "print(AutoDriftEnv.__name__)",
        ]
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.stdout.splitlines() == ["False", "AutoDriftEnv"]
