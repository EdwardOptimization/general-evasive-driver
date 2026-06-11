# M3226: B4 Minute-Scale Drive Structure Smoke

Status: completed. This is an auxiliary env-contract implementation smoke only.
It does not run training, mutate a driver, admit Track C, or make a validation
ranking, promotion, driver-performance, current-sim robustness, high-fidelity
sufficiency, paper, repair-success, feasibility-proof, or self-ID claim.

## Artifacts

- Preregistration:
  `experiments/feasibility_audit/minute_scale_drive_structure_prereg.json`
- Quick smoke:
  `experiments/feasibility_audit/minute_scale_drive_structure_smoke_quick.json`
- Full smoke:
  `experiments/feasibility_audit/minute_scale_drive_structure_smoke.json`
- Frame rows:
  `runs/feasibility_audit/minute_scale_drive_structure_smoke/frame_rows.csv`
- Script:
  `scripts/feasibility_audit/minute_scale_drive_structure_smoke.py`

## Implementation

M3226 separates raw obstacle-pass detection from pass-triggered episode
completion:

- `obstacle_passed_raw`: physical obstacle pass event.
- `obstacle_completed`: pass event plus `finish_on_pass=True`.

This preserves existing `finish_on_pass=True` completion behavior while
allowing long episodes to record a passed obstacle and continue to `max_steps`
when `finish_on_pass=False`.

The smoke uses a scripted zero-steer speed-hold controller only to keep the env
alive. It is not a deployable policy and is not a performance arm.

## Measurement

The full smoke ran 4 seeds at 3000 steps each, i.e. 60.0 s per episode at
`dt=0.02`. The profile uses a large-radius circle and wide track to keep the
test about episode structure rather than controller skill. The sequence within
each episode is:

1. Warmup gate visible in obstacle slot 0.
2. Warmup gate passed and deactivated.
3. Emergency obstacle appears later in the same episode.
4. Raw obstacle pass is recorded without `obstacle_completed`.
5. Episode continues to `max_steps`.

## Results

| readout | result |
|---|---:|
| full seeds | 4 |
| full frames | 12004 |
| duration per seed | 60.0 s |
| obs72 shape pass | true |
| finite observation pass | true |
| max-steps reached pass | true |
| warmup sequence pass | true |
| emergency obstacle sequence pass | true |
| raw-pass continuation pass | true |
| deterministic replay failures | 0 |
| warmup pass step range | 215-216 |
| emergency first step | 250 |
| raw pass step range | 991-999 |
| minimum post-pass continuation | 2001 steps |

## Decision

Accept M3226 as a completed B4 env-engineering milestone. The env now supports
the minute-scale structure needed for later work: same-episode familiarization,
later obstacle exposure, raw pass accounting, and post-pass continuation to
`max_steps`.

Future minute-scale controller outcome panels still need preregistered labels,
floors, criteria, and seed streams.
