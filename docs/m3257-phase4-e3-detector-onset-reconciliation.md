# M3257 Phase-4 E3 Detector-Onset Reconciliation

Status: completed.

## Verdict

- Full verdict: **detector_onset_reconciliation_completed**.
- Protocol gates passed: **true**.
- E2' dependency ready: **true**.
- Track F admitted: **false**.

## Measured

| readout | value |
|---|---:|
| Case rows | 24 / 24 |
| Trace rows | 3426 |
| Original early-fire rate | 0.5 |
| Original detector miss rate | 0.166667 |
| Original p90 latency | 1.346 s |
| Reconciled early-fire rate | 0 |
| Reconciled detector miss rate | 0.166667 |
| Corroborated early-fire rate | 0.5 |
| Uncorroborated detector-fire rate | 0 |
| Reconciled p90 latency | 1.346 s |

## Reconciled Definition

Use the detector fire step as the corrected onset when it occurs before the M3255 tire-slip truth onset and that tire truth later occurs within CORROBORATION_MAX_LEAD_STEPS; otherwise keep the M3255 tire-slip truth onset. If the detector fires and no tire truth follows inside the window, report an uncorroborated early detector fire.

## Reconciled By Axis

| axis | rows | miss rate | early-fire rate | median latency | p90 latency |
|---|---:|---:|---:|---:|---:|
| long | 12 | 0 | 0 | 0 steps | 0 steps |
| lat | 12 | 0.333333 | 0 | 60 steps | 88 steps |

## Inferred

M3257 reconciles the M3255 longitudinal early-fire anomaly by treating detector fires as actor-visible onset only when later corroborated by the frozen M3255 tire-slip event inside the pre-registered window. This makes the E2' detector definition explicit, but does not admit Track F or any training budget.

## Claim Boundary

Phase-4 E3-fix detector-onset reconciliation only: scripted Chrono Measurement-A brake/steer ramps compare the obs72 shortfall detector against M3255 tire-slip truth and a pre-registered detector-corroborated onset rule. This is zero training and makes no incumbent mutation, validation ranking, promotion, driver-performance, full high-fidelity sufficiency, paper, repair-success, robustness-result, feasibility-proof, Track-F-admission, or self-ID claim.

## Artifacts

- Preregistration: `experiments/feasibility_audit/phase4_e3_detector_onset_reconciliation_prereg.json`
- Full JSON: `experiments/feasibility_audit/phase4_e3_detector_onset_reconciliation.json`
- Case rows: `runs/feasibility_audit/phase4_e3_detector_onset_reconciliation/case_rows_full.csv`
- Trace rows: `runs/feasibility_audit/phase4_e3_detector_onset_reconciliation/trace_rows_full.csv`
- Metrics: `runs/feasibility_audit/phase4_e3_detector_onset_reconciliation/metrics_full.csv`
- Script: `scripts/feasibility_audit/phase4_e3_detector_onset_reconciliation.py`
