# M5 Emergency Avoidance

Last updated: 2026-05-20

## Goal

M5 introduces obstacle-avoidance scenarios where ordinary AEB may be unable to
stop before the obstacle. The first implementation step is a reproducible
scenario layer that labels cases before RL training starts.

## Scenario Labels

The scenario generator computes a conservative feasibility label from speed,
friction, obstacle distance, obstacle width, and simple acceleration envelopes:

- `aeb_feasible`: braking distance fits before the obstacle;
- `aes_feasible`: AEB is infeasible, but conventional lateral acceleration can
  clear the obstacle;
- `drift_required`: conventional AES is insufficient, but a high-sideslip
  lateral envelope can clear the obstacle;
- `unavoidable`: neither braking nor the high-sideslip lateral envelope clears
  the obstacle.

These are not final safety proofs. They are engineering labels for fixed-seed
benchmark buckets, so later RL and baseline policies are compared on the same
scenario classes.

## Implemented Infrastructure

Module:

```text
src/autodrift/scenarios.py
```

Command:

```bash
PYTHONPATH=src python -m autodrift.scenarios \
  --count 50 \
  --seed 7 \
  --require-aeb-infeasible \
  --run-dir runs/scenarios_m5_smoke
```

Smoke result:

| label | count |
| --- | ---: |
| aeb_feasible | 0 |
| aes_feasible | 27 |
| drift_required | 19 |
| unavoidable | 4 |

Artifacts:

```text
runs/scenarios_m5_smoke/scenarios.csv
runs/scenarios_m5_smoke/summary.json
```

The command-line entry point is also exposed as:

```bash
autodrift-scenarios
```

## Next Steps

M5 is only scaffolded. The next implementation work is:

- connect fixed obstacle scenarios to an environment task;
- add obstacle-relative observations and collision/min-distance metrics;
- add AEB-only and heuristic AES baselines;
- train/evaluate RL on fixed `aes_feasible`, `drift_required`, and
  `unavoidable` buckets;
- keep AEB-infeasible filtering explicit in every M5 benchmark manifest.
