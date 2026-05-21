# M120 Outcome-Critical Source-Diverse Miner

M119 showed that source-diverse matched-current action ambiguity still collapses
to a few old `9530/9540` pairs once outcome-level wrong-history degradation is
required. M120 moves to direct outcome-critical mining with snapshot-bank
relocation.

## Implementation

Updated selection and export in:

```text
src/autodrift/outcome_sensitive_corpus.py
src/autodrift/snapshot_bank_relocation.py
tests/test_outcome_sensitive_corpus.py
tests/test_snapshot_bank_relocation.py
```

Changes:

- added `outcome_physical_pair_key(...)`;
- added diversity limits to `select_outcome_sensitive_corpus(...)`;
- added CLI flags:
  - `--max-selected-per-physical-pair`;
  - `--max-selected-per-seed`;
  - `--export-only-accepted-outcomes`.

The export flag matters. Before M120, `snapshot_bank_relocation` could export
training snippets for rows that had margin gap but failed the visible/context
gate. M120 keeps old behavior available by default, but the M120 runs use clean
export so snippets are written only when the row is both visible-matched and
source-accepted.

Focused validation:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
python -m pytest -q tests/test_outcome_sensitive_corpus.py tests/test_snapshot_bank_relocation.py
```

Result:

```text
17 passed
```

## Commands

All formal M120 runs use:

```text
--episodes 10
--seed 9720
--nominal-friction-mu-range 0.85,1.15
--perturbed-friction-mu-range 0.25,0.35
--obstacle-perception-reveal-step 20
--obstacle-perception-reveal-distance 16
--bank-obstacle-distance-range 5,12
--bank-stride-steps 3
--bank-max-snapshots 30
--bank-max-pairs-per-seed 3
--snapshot-relocation-distances 10,11,12
--snapshot-relocation-lateral-offsets=-1
--snapshot-relocation-half-widths 0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4
--max-visible-distance 0.75
--max-response-distance 0.35
--min-margin-gap 0.005
--max-normal-margin 0.20
--max-continuation-steps 40
--probe-strategy steer_brake
--probe-steer-amplitude 0.25
--probe-brake-level 0.20
--probe-period-steps 20
--top-k 80
--max-selected-per-physical-pair 1
--max-selected-per-seed 2
--outcome-export-min-margin-gap 0.005
--export-only-accepted-outcomes
```

Strict context runs use:

```text
--max-context-distance 0.05
```

Relaxed diagnostic uses:

```text
--max-context-distance 0.30
```

Run directories:

```text
runs/m120_active_probe_snapshot_bank_m105_strict_exportclean_10ep_seed9720
runs/m120_active_probe_snapshot_bank_m105_relaxed_exportclean_10ep_seed9720
runs/m120_active_probe_snapshot_bank_m102_strict_exportclean_10ep_seed9720
runs/m120_active_probe_snapshot_bank_m62_strict_exportclean_10ep_seed9720
```

## Strict Result

| Policy | Candidates | Visible matches | Accepted outcome rows | Selected rows | Selected physical pairs | Snippets | Max gap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| M105 strict | 507 | 24 | 0 | 0 | 0 | 0 | 0.203195 |
| M102 strict | 507 | 24 | 0 | 0 | 0 | 0 | 0.014225 |
| M62 strict control | 507 | 24 | 0 | 0 | 0 | 0 | 0.008114 |

The `max_gap` column includes rows that failed strict visibility. Clean export
correctly writes zero snippets when accepted outcome rows are zero.

Strict gate result: negative. No checkpoint has accepted source-diverse
outcome-critical wrong-history rows under the strict context threshold.

## Relaxed Diagnostic

M105 relaxed context result:

| Metric | Value |
| --- | ---: |
| Candidates | 507 |
| Visible matches | 408 |
| Accepted outcome rows | 7 |
| Selected rows | 3 |
| Selected physical pairs | 3 |
| Selected seeds | 2 |
| Outcome snippets | 7 |
| Max accepted selected margin gap | 0.023294 |

Accepted rows are all perturbed-side margin-gap rows, not success drops. The
selected physical pairs are source-diverse only within two seeds:

| Seed | Nominal step | Perturbed step | Body x | Body y | Half width | Context dist | Gap | Perturbed normal margin | Perturbed wrong margin |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 9728 | 39 | 36 | 12 | -1 | 0.7 | 0.266893 | 0.023294 | 0.137907 | 0.114613 |
| 9721 | 34 | 31 | 11 | -1 | 0.7 | 0.268229 | 0.008188 | 0.054518 | 0.046330 |
| 9721 | 34 | 34 | 12 | -1 | 0.7 | 0.288742 | 0.005301 | 0.080729 | 0.075428 |

This is a useful diagnostic signal but not an admissible training surface:

- context distance is `0.246-0.289`, far above the strict `0.05` contract;
- selected seeds are only `2`, below the M120 target;
- there are no success drops;
- margin gaps are modest except one row.

## Interpretation

M120 is an infrastructure pass and a negative strict gate.

What improved:

- direct outcome mining now has explicit source-diverse selection;
- clean snippet export prevents non-visible rows from entering training data;
- relaxed context shows the direct miner can find margin-gap signal.

What failed:

- under strict current context matching, no M102/M105/M62 run produces accepted
  outcome-critical rows;
- the relaxed signal is blocked mostly by context mismatch, not by response
  mismatch;
- the relaxed signal covers too few seeds and physical pairs.

Do not train a wrong-history outcome objective from M120.

The next step should target context alignment directly: pair snapshots or choose
relocation geometry so road/obstacle context remains close while preserving the
wrong-history margin-gap signal.
