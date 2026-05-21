# M29 Matched Response-Critical Corpus

Last updated: 2026-05-21

## Motivation

M28 made the hidden-swap proof runnable, but it did not produce
outcome-critical ablations. On accepted matched cases, reset, zero-response, and
hidden-swap changed zero success outcomes. M29 turns that negative result into a
training/gate asset instead of stopping at the blocker.

The target is a seed corpus where:

- visible context is closely matched;
- hidden-state distance is nonzero;
- nominal and perturbed dynamics can differ in outcome;
- ablation deltas, action deltas, and return deltas are recorded for later
  training and gate design.

## Implementation

The corpus miner is implemented as:

```text
src/autodrift/matched_response_corpus.py
```

Script entry:

```text
autodrift-matched-response-corpus
```

It reads M28 `pairs.csv` and `replays.csv`, then writes:

- `candidate_pairs.csv`: all scored seed candidates;
- `scenario_corpus.csv`: selected seed corpus with `seed` as the first column;
- `variant_edges.csv`: normal-vs-ablation edges by source condition;
- `summary.json`: aggregate counts and score statistics;
- `manifest.json`: input and output artifact metadata.

The score favors seeds with ablation success changes first. If none exist, it
falls back to accepted condition-change and perturbed-failure seeds with high
hidden-state distance and low context-observation distance.

## Command

```bash
conda run -n autodrift python -m autodrift.matched_response_corpus \
  --pairs-csv runs/m28_hidden_swap_gate_seed4200/pairs.csv \
  --replays-csv runs/m28_hidden_swap_gate_seed4200/replays.csv \
  --top-k 40 \
  --min-hidden-state-distance 1.0 \
  --max-context-observation-distance 0.15 \
  --run-dir runs/m29_matched_response_corpus_seed4200
```

Run dir:

```text
runs/m29_matched_response_corpus_seed4200
```

Research-cycle log:

```text
runs/research/m29-response-critical-matched-corpus_20260521T031117Z/command.log
```

## Result

Summary:

- candidate seeds: 80;
- accepted visible matches: 74;
- selected seeds: 40;
- ablation success-change seeds: 0;
- ablation success-change edges: 0;
- nominal-vs-perturbed condition-change seeds: 26;
- perturbed-failure seeds: 28;
- accepted mean hidden-state distance: 1.354;
- accepted mean visible-observation distance: 0.410;
- selected score mean: 6.036.

Top selected seeds:

```text
4274, 4265, 4261, 4254, 4264, 4204, 4269, 4273, 4205, 4258
```

Conclusion: M29 confirms that M28 did not contain any ablation-outcome-critical
cases, but it did produce a useful matched hard corpus. The top selected seeds
are not proof of self-identification. They are training and gate-construction
material where perturbed low-friction dynamics fail while nominal dynamics pass
under closely matched visible context.

## Next Step

M30 should not repeat the M23 hard-only mistake. The next training path should
mix the M29 hard corpus with ordinary randomized resets, then evaluate:

- M26/M28 same-corpus aggregate success;
- M28 hidden-swap gate;
- M29 selected corpus success;
- broad same-seed obstacle benchmark versus envelope AES;
- reset, zero-response, and hidden-swap ablations.

If hard-corpus fine-tuning improves M29 but damages broad success, the sampler
must become mixed or curriculum-weighted before further training.
