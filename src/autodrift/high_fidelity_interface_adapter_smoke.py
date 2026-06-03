"""CLI smoke test for the HF0 current-sim backend adapter."""

from __future__ import annotations

import argparse
from pathlib import Path

from autodrift.artifacts import utc_timestamp, write_json
from autodrift.high_fidelity_interface import run_current_sim_adapter_smoke


def run_smoke(output_dir: Path, *, next_blocker: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = run_current_sim_adapter_smoke()
    summary.update(
        {
            "milestone": "m2474-high-fidelity-interface-current-sim-adapter-smoke",
            "generated_at_utc": utc_timestamp(),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HF0 current-sim adapter smoke.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_smoke(args.output_dir, next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"reset_count={summary['current_sim_reset_count']}")
    print(f"step_count={summary['current_sim_step_count']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
