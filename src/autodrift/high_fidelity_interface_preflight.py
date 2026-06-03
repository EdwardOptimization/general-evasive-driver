"""CLI preflight for the HF0 high-fidelity interface contract."""

from __future__ import annotations

import argparse
from pathlib import Path

from autodrift.artifacts import utc_timestamp, write_json
from autodrift.high_fidelity_interface import run_current_sim_p0_preflight


def run_preflight(output_dir: Path, *, seed: int, next_blocker: str) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = run_current_sim_p0_preflight(seed=seed)
    summary.update(
        {
            "milestone": "m2473-high-fidelity-interface-hf0-contract-implementation-preflight",
            "generated_at_utc": utc_timestamp(),
            "next_blocker": str(next_blocker),
        }
    )
    write_json(output_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run HF0 interface contract preflight.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=2473)
    parser.add_argument("--next-blocker", type=str, required=True)
    args = parser.parse_args()

    summary = run_preflight(args.output_dir, seed=int(args.seed), next_blocker=str(args.next_blocker))
    print(f"result_class={summary['result_class']}")
    print(f"status_pass={summary['status_pass']}")
    print(f"summary={args.output_dir / 'summary.json'}")


if __name__ == "__main__":
    main()
