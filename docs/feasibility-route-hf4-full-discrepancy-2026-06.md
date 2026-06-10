# HF4 Full Discrepancy Report: Current-Sim vs Chrono::Vehicle (2026-06-11)

## Status

- measurement: `chrono_hf4_full_discrepancy` — 256 rows (3 panels x 64 rows
  for the v4 incumbent, plus the feasible-only panel for the v5 candidate),
  same-scenario dual-backend execution.
- claim boundary: backend-comparison measurement only. No high-fidelity
  validation verdict, driver-performance verdict, promotion, robustness-result,
  feasibility-proof beyond the stated rows, or self-ID claim is made.
- determinism: 2 repeat rows (one per driver) byte-identical
  (`runs/feasibility_audit/chrono_hf4_full_summary.json`).
- artifacts: `experiments/feasibility_audit/chrono_hf4_full_rows.csv` (256
  rows), `runs/feasibility_audit/chrono_hf4_full_summary.json`,
  `runs/feasibility_audit/chrono_hf4_scenarios/` (exported same-scenario
  JSON), reproduce with
  `PYTHONPATH=src python scripts/feasibility_audit/chrono_hf4_full_discrepancy.py --resume`.

## Headline

**249/256 outcomes identical (97.3%). Zero success->collision and zero
success->offtrack flips in 256 rows: no current-sim safety conclusion
degrades under Chrono::Vehicle dynamics.** All 7 flips fall into two
attributable families that match the pre-registered known-differences list of
the backend (`docs/feasibility-route-hf-backend-2026-06.md`).

## Transition matrices (current-sim -> Chrono)

| panel:driver | success->success | failure->same failure | failure->success | success->speed_too_low | match |
|---|---|---|---|---|---|
| old:v4 | 56 | 7 (5 collision + 2 offtrack) | 0 | 1 | 63/64 |
| fresh:v4 | 53 | 8 (3 collision + 5 offtrack) | 2 | 1 | 61/64 |
| feasible_only:v4 | 59 | 3 offtrack | 1 | 1 | 62/64 |
| feasible_only:v5 | 60 | 3 offtrack | 0 | 1 | 63/64 |

Per-label Chrono success (v4): old aeb_feasible 54/55, fresh aeb_feasible
52/53, feasible_only aeb+aes 60/64 — identical to current-sim except the
liveness flips below.

## The three questions

### (a) Do feasible-row success rates hold under Chrono?

Yes for safety, with a small liveness caveat. Every feasible-row loss under
Chrono is a `speed_too_low` termination (3 unique rows: seed 401611/spec-0004,
501620/spec-0006, 601860/spec-0013 — the last one flips under both v4 and v5,
i.e. it is a backend property, not a driver property). These rows run at
~7.5-8.4 m/s mean in current-sim and ~5.3-5.8 m/s under the Chrono Sedan,
ending below the 1.0 m/s liveness threshold. Attribution: powertrain/drag
mapping (throttle-to-force vs the toy model's direct drive force), from the
known-differences list. **Zero feasible rows become collisions or offtrack.**

### (b) Do the unavoidable rows still fail (ceiling check)?

The old panel's 7 residual rows fail **identically** under Chrono (0007/0010/
0025/0026/0029 collision, 0013/0024 offtrack) — the measured ceiling of the
M3082 panel holds under higher-fidelity dynamics at full-panel scale.
One fresh-panel `unavoidable` row (seed 501531, spec-0008) flips
collision->success with margin +0.029 m: the Chrono Sedan's measured grip
surplus (~1.08-1.15x mu*g, TMeasy) is enough to clear a knife-edge row. This
confirms what the takeover documents already state: the unavoidability labels
and the ceiling are properties of the current-sim physics, not universal
constants.

### (c) Which rows flip, and does the direction match known differences?

| row | flip | attribution |
|---|---|---|
| old-0020 (401611), fresh-0021 (501620), feasible_only-0061 (601860, v4+v5) | success -> speed_too_low | powertrain/drag mapping (liveness, not safety) |
| fresh-0008 (501531, unavoidable) | collision -> success (+0.029 m) | grip surplus ~1.08-1.15x mu*g |
| fresh-0053 (501820) | offtrack -> success | low-speed spin-out mode is toy-model-specific (TMeasy + load transfer does not reproduce it) |
| feasible_only-0024 (602631) | offtrack -> success (+0.218 m) | grip surplus on a marginal tracking row |

Notable: the two rows the v5 candidate was designed to fix (fresh-0053,
feasible_only-0024) do not fail under Chrono at all — part of that failure
mode is a current-sim artifact — while v5 itself holds parity under Chrono
(60/64 on the feasible-only panel, no high-fidelity regression).

## Implications

1. The project's qualitative safety conclusions (feasible-row competence,
   residual-row infeasibility, failure-mode direction) transfer to a
   higher-fidelity vehicle model; absolute success rates remain sim-specific
   as always stated.
2. The next fidelity-sensitivity items, in order of observed impact: the
   powertrain/low-speed liveness mapping (3 flips), grip calibration
   (2 flips), then the unmapped parameters (inertia, cg, tire stiffness) which
   produced no observed outcome flips at this scale.
3. Route C (HF3/HF4) is no longer blocked or hypothetical: dual-backend
   same-scenario measurement is now a one-command operation.
