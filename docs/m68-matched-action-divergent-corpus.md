# M68 Matched Action-Divergent Corpus

M67-E did not produce a meaningful privileged-teacher upper-bound gap. M68 adds
a corpus miner for a sharper question:

```text
Can we find cases where the current visible human-view state is nearly the same,
but different hidden dynamics, wrong recurrent history, or swapped privileged
teacher context changes the action?
```

This is not a student-training result. It is a proof-surface harness for
deciding whether the current corpus contains self-identification-critical
states.

## Harness

New module:

```text
src/autodrift/matched_action_corpus.py
```

Inputs:

- env config;
- recurrent checkpoint;
- seed list or episode count;
- nominal and perturbed friction/randomization conditions;
- target obstacle distance for snapshot selection;
- visible-state thresholds;
- action-divergence threshold.

For each seed, the harness:

1. runs nominal and perturbed conditions to a decision snapshot near the target
   obstacle distance;
2. compares only the first 72 deployable human-view dimensions for visible-state
   matching;
3. separately checks response distance and context distance;
4. computes action divergence for:
   - nominal action versus perturbed action;
   - source observation with wrong recurrent history;
   - source visible observation with paired privileged packet;
5. writes:
   - `matched_pairs.csv`;
   - `action_divergent_snippets.csv`;
   - `summary.csv`;
   - `summary.json`;
   - `manifest.json`.

The split metrics are important. A pair is not good self-ID evidence just
because nominal and perturbed actions differ. The harness records whether the
divergence comes from:

```text
paired current observations
wrong recurrent history
swapped privileged dynamics packet
```

Only the latter two are directly useful for the self-identification proof.

## Validation

Focused tests:

```text
conda run -n autodrift pytest -q tests/test_matched_action_corpus.py
```

Result:

```text
4 passed
```

Compile and whitespace checks:

```text
python -m compileall -q src tests
git diff --check
```

Both passed during harness development.

## Smoke Command

The smoke run uses the best M67-E checkpoint, `m67e_004`, on the M65
response-necessity corpus:

```text
conda run -n autodrift python -m autodrift.matched_action_corpus \
  --env-config configs/ppo_m67e_warm_started_privileged_teacher.json \
  --checkpoint runs/ppo_m67e_warm_privileged_teacher_seed3267/checkpoints/checkpoint_step_4096.pt \
  --seed-csv runs/m65_response_necessity_corpus_seed3600/scenario_corpus.csv \
  --seed 6800 \
  --device cpu \
  --top-k 20 \
  --max-visible-distance 0.75 \
  --max-response-distance 0.25 \
  --max-context-distance 0.05 \
  --min-action-distance 0.05 \
  --run-dir runs/m68_matched_action_corpus_split_smoke_m65_seed6800
```

Strict matching means all three checks must pass:

```text
visible_observation_distance <= 0.75
visible_response_distance <= 0.25
visible_context_distance <= 0.05
```

## Smoke Result

Summary:

| Metric | Value |
| --- | ---: |
| Pairs | 26 |
| Accepted visible matches | 10 |
| Accepted action-divergent pairs | 6 |
| Accepted paired-action divergent pairs | 6 |
| Accepted wrong-history divergent pairs | 1 |
| Accepted privileged-packet divergent pairs | 0 |
| Mean visible distance | 0.300683 |
| Mean visible context distance | 0.014697 |
| Mean hidden-state distance | 1.156545 |
| Mean privileged-tail distance | 0.681186 |
| Mean paired-action distance | 0.039916 |
| Mean wrong-history action distance | 0.019980 |
| Mean privileged-packet action distance | 0.000075 |
| Max action distance | 0.103245 |

Top action-divergent snippets:

| Seed | Visible Dist | Response Dist | Context Dist | Paired Action Dist | Wrong-History Dist | Privileged-Packet Dist | Max Action Dist |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3628 | 0.227254 | 0.225243 | 0.030168 | 0.103245 | 0.054057 | 0.000055 | 0.103245 |
| 3663 | 0.203032 | 0.202056 | 0.019885 | 0.098865 | 0.039029 | 0.000052 | 0.098865 |
| 3627 | 0.203465 | 0.202697 | 0.017662 | 0.073995 | 0.031045 | 0.000037 | 0.073995 |
| 3607 | 0.239732 | 0.239065 | 0.017877 | 0.068694 | 0.022523 | 0.000100 | 0.068694 |
| 3648 | 0.234358 | 0.234041 | 0.012184 | 0.064247 | 0.029406 | 0.000065 | 0.064247 |
| 3649 | 0.197566 | 0.197025 | 0.014621 | 0.057156 | 0.020476 | 0.000063 | 0.057156 |

## Interpretation

M68 validates the mining harness, but the M65 smoke result is still a negative
self-ID diagnostic.

Useful signals:

- the harness can find same-geometry / near-same-visible-state pairs;
- context distance is small on accepted pairs;
- hidden-state distance is nontrivial;
- one accepted pair crosses the wrong-history action-divergence threshold.

Weak signals:

- action divergence is mostly nominal-current-response versus
  perturbed-current-response;
- the accepted pairs still have response distances around `0.20` to `0.24`;
- swapping the privileged hidden-dynamics packet barely changes action;
- no accepted pair passes the privileged-packet divergence threshold.

Conclusion:

```text
M67-E's privileged branch is not action-relevant enough to serve as a teacher.
The current M65 corpus contains some paired-action differences, but they are not
yet clean evidence that hidden dynamics alone changes the right action.
```

## Next Step

Do not train the deployable student yet.

Next milestone should broaden and sharpen matched mining:

- search fresh random seeds beyond M65;
- sweep low-friction, weak-brake, and slow-actuator perturbation axes;
- require stricter current-response matching where possible;
- rank pairs by wrong-history or privileged-packet action divergence, not just
  nominal-versus-perturbed action distance;
- only after enough causal pairs exist, build wrong-history continuation gates
  and teacher-student distillation.
