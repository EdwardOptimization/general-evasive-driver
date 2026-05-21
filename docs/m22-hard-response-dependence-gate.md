# M22 Hard Response-Dependence Gate

Last updated: 2026-05-21

## Motivation

M21 improves aggregate obstacle avoidance but still does not prove that the
policy depends on deployable response channels. The response-critical actor can
solve many near-threshold cases using context plus a default recurrent state:
zeroing response channels does not reliably reduce success.

The next gate should make that shortcut fail. Instead of only changing the
actor, M22 should mine or construct paired scenarios where the visible geometry
is identical but the correct steering and drive/brake correction differs
because of hidden tire, actuator, brake, or road response.

## Requirement

M22 must preserve the clean project rule:

- no privileged actor inputs;
- no `mu`, vehicle parameters, `speed_ref`, `beta_target`, explicit `beta`, or
  scenario label in actor observations;
- no checkpoint shape compatibility path;
- response dependence is measured by ablation, not assumed from architecture.

## Proposed Work

1. Mine a hard paired corpus from existing scenario seeds and hidden
   randomization ranges.
2. Keep only pairs where `m21_503` or `m21_602` normal inference succeeds in at
   least one hidden condition and a response-masked or reset variant changes the
   outcome.
3. Add a training or fine-tuning config that oversamples this hard corpus while
   preserving the current clean 15-value actor frame.
4. Evaluate normal, reset, zero-current-response, and zero-all-response
   policies on actuator-response, friction, and same-corpus gates.

## Pass Criteria

The next checkpoint must improve or preserve M21 aggregate performance while
making response ablation visibly worse:

- same-corpus obstacle success at least `0.500`;
- actuator-response perturbed success at least `0.450`;
- M13 friction perturbed success at least `0.450`;
- response-masked success at least `0.050` below normal on a hard paired gate;
- hidden-reset success at least `0.050` below normal on a hard paired gate.

If the mined corpus is too sparse, the blocker should be documented as a gate
construction problem before adding more model complexity.

## Harness

M22 adds:

```text
src/autodrift/hard_response_corpus.py
```

The CLI mines hard seeds from paired gate `episodes.csv` artifacts. A seed is
selected when normal recurrent inference succeeds in at least one hidden
condition and at least one reset or response-masked policy changes success for
that same seed. The output is a normal seed CSV, so the existing paired gate can
replay it directly.

Command for `m21_503`:

```bash
conda run -n autodrift python -m autodrift.hard_response_corpus \
  --episodes-csv runs/m21_top_actuator_response_gate_seed3000/episodes.csv \
  --episodes-csv runs/m21_top_friction_gate_seed3000/episodes.csv \
  --normal-policy m21_503 \
  --ablation-policy m21_503_reset \
  --ablation-policy m21_503_zero_current \
  --ablation-policy m21_503_zero_all \
  --run-dir runs/m22_hard_response_corpus_m21_503_seed3000
```

Result:

- selected hard seeds: 7;
- success-changing rows in selected pairs: 10;
- corpus: `runs/m22_hard_response_corpus_m21_503_seed3000/scenario_corpus.csv`;
- pair details: `runs/m22_hard_response_corpus_m21_503_seed3000/hard_pairs.csv`.

Command for `m21_602`:

```bash
conda run -n autodrift python -m autodrift.hard_response_corpus \
  --episodes-csv runs/m21_top_actuator_response_gate_seed3000/episodes.csv \
  --episodes-csv runs/m21_top_friction_gate_seed3000/episodes.csv \
  --normal-policy m21_602 \
  --ablation-policy m21_602_reset \
  --ablation-policy m21_602_zero_current \
  --ablation-policy m21_602_zero_all \
  --run-dir runs/m22_hard_response_corpus_m21_602_seed3000
```

Result:

- selected hard seeds: 6;
- success-changing rows in selected pairs: 8;
- corpus: `runs/m22_hard_response_corpus_m21_602_seed3000/scenario_corpus.csv`.

## Gate Result

M21_503 hard actuator gate:

| policy | pairs | nominal success | perturbed success |
| --- | ---: | ---: | ---: |
| m21_503 | 7 | 1.000 | 0.714 |
| m21_503_reset | 7 | 0.143 | 0.714 |
| m21_503_zero_current | 7 | 0.857 | 0.571 |
| m21_503_zero_all | 7 | 0.857 | 0.571 |

M21_503 hard friction gate:

| policy | pairs | nominal success | perturbed success |
| --- | ---: | ---: | ---: |
| m21_503 | 7 | 1.000 | 0.714 |
| m21_503_reset | 7 | 1.000 | 0.571 |
| m21_503_zero_current | 7 | 1.000 | 0.714 |
| m21_503_zero_all | 7 | 1.000 | 0.714 |

M21_602 hard actuator gate:

| policy | pairs | nominal success | perturbed success |
| --- | ---: | ---: | ---: |
| m21_602 | 6 | 0.833 | 0.667 |
| m21_602_reset | 6 | 0.167 | 0.667 |
| m21_602_zero_current | 6 | 0.833 | 0.667 |
| m21_602_zero_all | 6 | 0.833 | 0.667 |

M21_602 hard friction gate:

| policy | pairs | nominal success | perturbed success |
| --- | ---: | ---: | ---: |
| m21_602 | 6 | 1.000 | 0.667 |
| m21_602_reset | 6 | 1.000 | 0.000 |
| m21_602_zero_current | 6 | 1.000 | 0.667 |
| m21_602_zero_all | 6 | 1.000 | 0.667 |

Conclusion: M22 succeeds as a gate-construction step. The mined hard actuator
corpus exposes response-channel dependence for `m21_503`: response masking
drops nominal success by `0.143` and perturbed success by `0.143`, while
hidden-state reset drops nominal success by `0.857`. The hard friction corpus
mainly exposes hidden-state dependence, not response-mask dependence. The next
step should scale the hard corpus and add a training sampler or fine-tuning path
that oversamples these hard cases without adding privileged actor inputs.
