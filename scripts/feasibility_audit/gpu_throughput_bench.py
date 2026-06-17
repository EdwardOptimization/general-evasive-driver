"""Throughput bench for gpu_sim rung-0 (the PRETRAIN config): eager vs torch.compile-fused env-steps/s
across batch sizes, + the eager-vs-compiled gear-flip correctness caveat. Commits the JSON so the design
roadmap leans on a MEASURED number, not the prose "582M" (design §6 T0 deliverable #1).

    python scripts/feasibility_audit/gpu_throughput_bench.py            # GPU; writes runs/.../gpu_throughput.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
torch.set_default_dtype(torch.float32)

from autodrift.gpu_sim import FidelityConfig, build_model  # noqa: E402

OUT = ROOT / "runs/feasibility_audit/phase4_f2/gpu_throughput.json"
DEV = "cuda" if torch.cuda.is_available() else "cpu"


def _bench(step, model, cfg, N, steps=100, warm=30):
    P = model.make_param_batch(model.build_phys(cfg), N, mu=0.5, device=DEV, dtype=torch.float32)
    vx0 = torch.full((N,), 8.0, device=DEV); z = torch.zeros(N, device=DEV)
    st, gear = model.init_state(vx0, z, z, P); act = torch.zeros(N, 3, device=DEV)
    for _ in range(warm):
        st, gear, _ = step(st, act, gear, P, 0.02)
    if DEV == "cuda":
        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    for _ in range(steps):
        st, gear, _ = step(st, act, gear, P, 0.02)
    if DEV == "cuda":
        torch.cuda.synchronize()
    dt = time.time() - t0
    vram = torch.cuda.max_memory_allocated() / 1e9 if DEV == "cuda" else 0.0
    return N * steps / dt, vram


def main():
    cfg = FidelityConfig(rung=0, vehicle_variant="sedan_tmeasy")
    model = build_model(cfg)
    eager = model.physics_step
    compiled = torch.compile(model.physics_step, mode="default", dynamic=False)
    print(f"device={DEV}  rung-0={model.name}")
    rows = []
    for N in [4096, 16384, 65536, 262144, 2097152]:
        e, ev = _bench(eager, model, cfg, N)
        try:
            c, cv = _bench(compiled, model, cfg, N, warm=50)
            sp = c / e
        except Exception as ex:  # noqa: BLE001
            c, cv, sp = float("nan"), 0.0, float("nan")
            print(f"  N={N:8d}: compile failed {str(ex)[:40]}")
        rows.append(dict(N=N, eager_Mst_s=e / 1e6, compiled_Mst_s=c / 1e6, speedup=sp, vram_gb=cv))
        print(f"  N={N:8d}: eager {e/1e6:7.2f} M/s | compiled {c/1e6:8.2f} M/s | {sp:6.1f}x | {cv:5.2f} GB")
    payload = dict(device=DEV, rung=model.name, dt=0.02, note="env-steps/s; compiled=torch.compile default",
                   caveat="compiled flips ~3% of envs at gear thresholds (discrete switch on raw float compare);"
                          " benign for RL training (DR-like), certify runs eager.", rows=rows)
    OUT.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
