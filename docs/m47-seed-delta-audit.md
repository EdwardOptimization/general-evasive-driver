# M47 Seed-Delta Audit

Last updated: 2026-05-21

## Motivation

M46 gave a mixed result: it improved the M38 response-critical corpus by one
seed but regressed the broad same-seed sweep by one seed. Aggregate success
alone hides whether those changes come from the same scenario family. M47 adds
a seed-level audit harness before designing another training objective.

## Harness

New CLI:

```text
autodrift.seed_delta_audit
```

It reads a benchmark `episodes.csv`, compares one baseline policy against one
or more candidate policies on shared seeds, and writes:

- `seed_deltas.csv`;
- `policy_delta_summary.csv`;
- `group_delta_summary.csv`;
- `manifest.json`.

The audit reports per-seed outcome class:

- `improved`: baseline fails, candidate succeeds;
- `regressed`: baseline succeeds, candidate fails;
- `unchanged_success`;
- `unchanged_failure`.

It also groups deltas by obstacle label, friction bucket, mass bucket,
cg bucket, brake bucket, tire bucket, and steering delay bucket.

## Commands

M38 audit:

```bash
conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m46_m38_corpus_checkpoint_sweep_seed4300/episodes.csv \
  --baseline-policy m37_102 \
  --candidate-policy m46_077 \
  --candidate-policy m46_200 \
  --run-dir runs/m47_m46_m38_seed_delta_audit_seed4300
```

Broad audit:

```bash
conda run -n autodrift python -m autodrift.seed_delta_audit \
  --episodes-csv runs/m46_broad_checkpoint_sweep_seed3000/episodes.csv \
  --baseline-policy m37_102 \
  --candidate-policy m46_077 \
  --candidate-policy m46_200 \
  --run-dir runs/m47_m46_broad_seed_delta_audit_seed3000
```

## M38 Result

| Candidate | Pairs | Baseline success | Candidate success | Improved | Regressed |
| --- | ---: | ---: | ---: | ---: | ---: |
| M46_077 | 80 | 0.6250 | 0.6375 | 1 | 0 |
| M46_200 | 80 | 0.6250 | 0.6375 | 1 | 0 |

The single improved seed is 4327 for both M46_077 and M46_200:

| Seed | Label | mu | initial mu | mass | cg | brake | tire | steer tau | M37 return | M46_077 return | M46_200 return |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 4327 | unavoidable | 1.137 | 0.658 | nominal | front | weak | weak | slow | 0.441 | 54.718 | 54.033 |

This is a high-friction current-state case after a friction step, but with weak
braking, weak tire stiffness, front cg shift, and slow steering. M37_102 and
M42_028 collide; M46_053, M46_077, M46_126, M46_176, and M46_200 complete the
obstacle. The improvement appears only after M46 has trained enough, not at the
earliest checkpoint.

## Broad Result

| Candidate | Pairs | Baseline success | Candidate success | Improved | Regressed |
| --- | ---: | ---: | ---: | ---: | ---: |
| M46_077 | 40 | 0.8250 | 0.8000 | 0 | 1 |
| M46_200 | 40 | 0.8250 | 0.8000 | 0 | 1 |

The single regressed seed is 3037 for both M46_077 and M46_200:

| Seed | Label | mu | initial mu | mass | cg | brake | tire | steer tau | M37 return | M46_077 return | M46_200 return |
| ---: | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: | ---: | ---: |
| 3037 | unavoidable | 0.340 | 0.324 | nominal | nominal | strong | nominal | slow | 91.586 | 36.802 | 35.844 |

This is a low-friction unavoidable case with strong brakes, nominal tire
stiffness, nominal cg, and slow steering. M30_053, M37_102, and M42_028
complete it; M46_077 and M46_200 collide. The paired-hidden action contrast
therefore traded broad low-friction robustness for a narrow high-friction
unavoidable improvement.

## Interpretation

The M46 loss is not the right next objective by itself. It pushes action means
apart for fixed offline hidden vectors, but the evidence says the resulting
policy change is not a general self-identification improvement:

- hidden-swap outcome changes remain zero;
- the M38 success gain is one seed;
- the broad success loss is one different seed;
- both changed seeds are unavoidable cases with slow steering, but opposite
  current friction and different brake/tire regimes.

The next objective should use continuation-level evidence from actual
closed-loop rollouts. A useful M48 direction is to mine transition snippets
around seeds 4327 and 3037, then train or select against a criterion that
preserves low-friction unavoidable completion while improving high-friction
weak-actuator completion. Static hidden-vector action separation is too indirect
to be trusted alone.
