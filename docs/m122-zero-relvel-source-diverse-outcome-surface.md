# M122 Zero-Relvel Source-Diverse Outcome Surface

M121 showed that zeroing obstacle relative velocity restores strict
context-aligned wrong-history outcome rows, but the 30-episode run still lacked
source diversity. M122 repeats the same strict zero-relvel miner at 60 episodes
before training any new objective.

## Question

Does the M121 zero-relvel strict profile produce a source-diverse
wrong-history outcome surface when sampled broadly enough, while keeping the
M62 control clean?

Admission requires:

- strict context threshold remains `<= 0.05`;
- M105 selected rows cover at least `6` physical pairs and `5` seeds/source
  decision steps;
- accepted rows include real outcome degradation, not only non-visible margin
  gaps;
- M62 control is not admitted under the same miner settings.

This is a corpus admission gate only. Passing M122 does not admit a driver
checkpoint.

## Commands

M105 60-episode strict zero-relvel run:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m autodrift.snapshot_bank_relocation \
  --env-config configs/m121_human_view_zero_obstacle_relvel.json \
  --checkpoint runs/m105_anchor10_outcome_coupling_smoke_seed9710/optimized_checkpoint.pt \
  --episodes 60 \
  --seed 9720 \
  --device cpu \
  --nominal-friction-mu-range 0.85,1.15 \
  --perturbed-friction-mu-range 0.25,0.35 \
  --obstacle-perception-reveal-step 20 \
  --obstacle-perception-reveal-distance 16 \
  --bank-obstacle-distance-range 5,12 \
  --bank-stride-steps 3 \
  --bank-max-snapshots 30 \
  --bank-max-pairs-per-seed 3 \
  --snapshot-relocation-distances 10,11,12 \
  --snapshot-relocation-lateral-offsets=-1 \
  --snapshot-relocation-half-widths 0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.35 \
  --max-context-distance 0.05 \
  --min-margin-gap 0.005 \
  --max-normal-margin 0.20 \
  --max-continuation-steps 40 \
  --probe-strategy steer_brake \
  --probe-steer-amplitude 0.25 \
  --probe-brake-level 0.20 \
  --probe-period-steps 20 \
  --top-k 200 \
  --max-selected-per-physical-pair 1 \
  --max-selected-per-seed 2 \
  --outcome-export-min-margin-gap 0.005 \
  --export-only-accepted-outcomes \
  --run-dir runs/m122_zero_relvel_m105_strict_60ep_seed9720
```

M62 60-episode control run uses the same command except:

```text
--checkpoint runs/m62_m37_m61_032_interpolated_checkpoints/checkpoints/alpha_0_25.pt
--run-dir runs/m122_zero_relvel_m62_strict_60ep_seed9720
```

## Results

| Run | Candidates | Visible matches | Accepted rows | Success-drop pairs | Selected rows | Selected physical pairs | Selected seeds | Snippets | Max snippet gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M105 zero-relvel strict 60ep | 3134 | 1680 | 12 | 9 | 6 | 6 | 5 | 11 | 0.027255 |
| M62 zero-relvel strict 60ep | 3134 | 1608 | 0 | 0 | 0 | 0 | 0 | 0 | 0.000000 |

M105 accepted rows cover:

```text
accepted rows: 12
accepted seeds: 5
accepted physical pairs: 6
accepted source steps: 8
source steps: 24, 27, 30, 33, 36, 39, 42, 48
```

Selected M105 rows:

| Seed | Nominal step | Perturbed step | Body x | Half width | Response dist | Context dist | Gap | Perturbed normal margin | Perturbed wrong margin | Success drop |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9741 | 27 | 27 | 12 | 0.9 | 0.151218 | 0.041485 | 0.026935 | 0.010214 | -0.016721 | 1 |
| 9728 | 39 | 36 | 12 | 0.8 | 0.169944 | 0.026702 | 0.026296 | 0.043447 | 0.017151 | 0 |
| 9770 | 30 | 33 | 11 | 0.8 | 0.305324 | 0.020888 | 0.014164 | 0.060487 | 0.046322 | 0 |
| 9724 | 48 | 42 | 12 | 1.0 | 0.228495 | 0.012615 | 0.006110 | 0.173363 | 0.167253 | 0 |
| 9728 | 36 | 36 | 12 | 0.8 | 0.182813 | 0.017705 | 0.005379 | 0.043447 | 0.038068 | 0 |
| 9752 | 27 | 24 | 11 | 0.7 | 0.264834 | 0.005427 | 0.001887 | 0.000839 | -0.001047 | 1 |

The last selected row has `max_margin_gap < 0.005` because it is accepted by a
success drop, not by margin-gap threshold.

All exported M105 intervention snippets are perturbed-source rows:

```text
source_conditions: {'perturbed': 11}
```

This matters for interpretation. M122 admits a low-friction-side
wrong-history corpus, not a symmetric nominal/perturbed corpus.

## Decision

M122 admits the M105 zero-relvel strict corpus for the next objective-sanity
experiment:

- M105 meets the source-diversity gate with `6` selected physical pairs, `5`
  selected seeds, and `8` accepted source steps;
- M105 includes real outcome degradation with `9` success-drop pairs before
  source-diverse selection;
- M62 control remains clean with zero accepted rows and zero exported snippets;
- strict context stays at `0.05`, and obstacle relative velocity is zero by
  profile.

Do not claim driver success from this result. The next step is an
objective-sanity run that uses the M122 snippets with retention anchoring, then
checks behavior and hidden-belief gates before any PPO continuation.
