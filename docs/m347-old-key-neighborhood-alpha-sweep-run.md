# M347 Old-Key Neighborhood Alpha Sweep Run

M347 runs the no-PPO old-key neighborhood alpha sweep designed in M346. It does
not train, repair, promote, or change actor inputs.

## Tooling Note

The first attempt used the generic `critical_key_replay_guard` path over all
selected alpha checkpoints. That path was too slow for this exact compact
surface: after about nine minutes it had not completed the first policy because
it reruns full snapshot-bank pairing and relocation-grid mining.

M347 therefore added a targeted replay runner:

```text
src/autodrift/old_key_neighborhood_targeted_replay.py
tests/test_old_key_neighborhood_targeted_replay.py
```

This runner keeps the same closed-loop policy history per checkpoint, but
replays only the exact 40 compact old-key rows instead of rediscovering the full
bank/grid surface.

## Reference Cases

The exact compact reference cases were exported to:

```text
runs/m347_old_key_alpha_sweep/compact_reference_cases.csv
```

Rows:

```text
40
```

All compact rows are `perturbed` source-condition rows, with paired nominal
history steps.

## Targeted Replay

Command shape:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.old_key_neighborhood_targeted_replay \
  --reference-manifest runs/m341_old_key_neighborhood_block_a_seed9860/manifest.json \
  --compact-corpus-csv runs/m341_old_key_neighborhood_mining/old_key_neighborhood_compact_corpus.csv \
  --checkpoint-policy m335_a0_0075=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_0075.pt \
  --checkpoint-policy m335_a010=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_01.pt \
  --checkpoint-policy m335_a020=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_02.pt \
  --checkpoint-policy m335_a050=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_05.pt \
  --checkpoint-policy m335_a100=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_1.pt \
  --checkpoint-policy m335_a200=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_0_2.pt \
  --checkpoint-policy m335_a1000=runs/m335_m333_to_repaired_gap_bounded_interpolation/checkpoints/alpha_1.pt \
  --device cpu \
  --run-dir runs/m347_old_key_alpha_sweep/targeted_replay
```

Policy replay summary:

| Policy | Cases | Found | Accepted | Policy pass | Normal success | Gap mean | Gap min | Gap delta mean | Gap delta min |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| m335_a0_0075 | 40 | 40 | 40 | true | 40 | 0.008472 | 0.000771 | 0.000007 | -0.000049 |
| m335_a010 | 40 | 40 | 40 | true | 40 | 0.008474 | 0.000771 | 0.000010 | -0.000065 |
| m335_a020 | 40 | 40 | 39 | false | 40 | 0.008481 | 0.000768 | 0.000017 | -0.000130 |
| m335_a050 | 40 | 40 | 39 | false | 40 | 0.008483 | 0.000761 | 0.000019 | -0.000325 |
| m335_a100 | 40 | 40 | 38 | false | 40 | 0.008479 | 0.000750 | 0.000015 | -0.000649 |
| m335_a200 | 40 | 40 | 38 | false | 40 | 0.008441 | 0.000726 | -0.000023 | -0.001289 |
| m335_a1000 | 40 | 40 | 25 | false | 37 | 0.006273 | -0.009512 | -0.002191 | -0.050660 |

## Replayable Gate Results

Adapter:

```text
src/autodrift/old_key_neighborhood_replay_gate.py
```

Aggregate artifact:

```text
runs/m347_old_key_alpha_sweep/summary.json
runs/m347_old_key_alpha_sweep/alpha_sweep_summary.csv
```

| Policy | Alpha | Pass | Repair needed | Accepted regressions | Normal-success regressions | Gap p10 | Gap min |
| --- | ---: | --- | --- | ---: | ---: | ---: | ---: |
| m335_a0_0075 | 0.0075 | true | false | 0 | 0 | 0.0 | 0.0 |
| m335_a010 | 0.01 | true | false | 0 | 0 | -0.000006 | -0.000016 |
| m335_a020 | 0.02 | false | false | 1 | 0 | -0.000030 | -0.000082 |
| m335_a050 | 0.05 | false | false | 1 | 0 | -0.000101 | -0.000277 |
| m335_a100 | 0.10 | false | true | 2 | 0 | -0.000352 | -0.000600 |
| m335_a200 | 0.20 | false | true | 2 | 0 | -0.000797 | -0.001333 |
| m335_a1000 | 1.0 | false | true | 15 | 3 | -0.004040 | -0.050620 |

The first failing condition for `alpha=0.02` is not gap magnitude; it is one
accepted-case regression:

```text
candidate_accepted_regressions>0
```

## Interpretation

The distributional old-key neighborhood gate is less restrictive than the old
singleton `9944` floor:

```text
old accepted alpha: 0.0075
new largest old-key passing alpha: 0.01
first failing alpha: 0.02
```

But the trust region is still tight. This is not evidence that `alpha=0.01` is
promotable. It only means `alpha=0.01` deserves the next exact/source-diverse
and first-replay probe.

The repaired endpoint remains rejected:

```text
alpha=1.0 accepted regressions: 15
alpha=1.0 normal-success regressions: 3
alpha=1.0 repair-needed: true
```

So the new distributional gate is not too weak.

## Tests

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q \
  tests/test_old_key_neighborhood_targeted_replay.py \
  tests/test_old_key_neighborhood_replay_gate.py \
  tests/test_old_key_neighborhood_gate.py
```

Result:

```text
15 passed
```

## Decision

M347 passes as a no-PPO proof-gate run.

Decision:

```text
admit_m348_exact_source_diverse_probe_for_m335_a010
```

M348 should evaluate `m335_a010` with exact M297/M270, source-diverse protected
gates, and first replay gates. It must not promote directly from M347.
