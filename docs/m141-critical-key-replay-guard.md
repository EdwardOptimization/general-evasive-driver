# M141 Critical-Key Replay Guard

M141 turns the M140 key-survival diagnosis into a cheap exact replay guard.
The guard is meant to run before expensive strict 60-episode miners or PPO
continuation. It protects selected M133 near-threshold keys whose survival is
not guaranteed by fixed logprob or fixed action-MSE objectives.

## Implementation

New module:

```text
src/autodrift/critical_key_replay_guard.py
```

The CLI:

```text
python -m autodrift.critical_key_replay_guard
```

loads a reference strict-miner manifest, derives protected cases from reference
`outcome_sensitive_snippets.csv`, reruns only the protected seed/relocation
cases for each checkpoint policy, and reports whether each policy preserves the
protected accepted row.

It does not change actor observations. The same deployable actor input contract
is used; hidden dynamics are only used by the existing gate harness to create
nominal/perturbed evaluation conditions.

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src \
  python -m pytest -q tests/test_critical_key_replay_guard.py
```

Result: `2 passed`.

## Command

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m autodrift.critical_key_replay_guard \
  --reference-manifest runs/m133_zero_relvel_s60_strict_60ep_seed9900/manifest.json \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9900/outcome_sensitive_snippets.csv \
  --reference-cases-csv runs/m133_zero_relvel_s60_strict_60ep_seed9920/outcome_sensitive_snippets.csv \
  --case-key '9944|perturbed|28|28' \
  --checkpoint-policy m132_s60=runs/m132_margin_retention_s60_anchor20_seed9841/optimized_checkpoint.pt \
  --checkpoint-policy m139_s20_snip1000=runs/m139_m136_s20_env20_snip1000_seed7141/optimized_checkpoint.pt \
  --checkpoint-policy m139_s40_snip500=runs/m139_m136_s40_env20_snip500_seed7139/optimized_checkpoint.pt \
  --checkpoint-policy m139_s40_snip100=runs/m139_m136_s40_env20_snip100_seed7140/optimized_checkpoint.pt \
  --reference-policy m132_s60 \
  --device cpu \
  --run-dir runs/m141_critical_key_replay_guard_seed9944
```

Artifacts:

```text
runs/m141_critical_key_replay_guard_seed9944/protected_cases.csv
runs/m141_critical_key_replay_guard_seed9944/guard_results.csv
runs/m141_critical_key_replay_guard_seed9944/policy_summary.csv
runs/m141_critical_key_replay_guard_seed9944/summary.json
```

## Protected Case

| key | distance | lateral | half width | reference margin gap |
| --- | ---: | ---: | ---: | ---: |
| `9944|perturbed|28|28` | 11.0 | -1.0 | 0.9 | 0.005196 |

This is the M140 shared lost key.

## Result

| policy | accepted cases | pass | margin gap |
| --- | ---: | --- | ---: |
| M132 s60 | 1 / 1 | yes | 0.005196 |
| M139 s20 snip1000 | 0 / 1 | no | 0.004675 |
| M139 s40 snip500 | 0 / 1 | no | 0.004829 |
| M139 s40 snip100 | 0 / 1 | no | 0.004576 |

`summary.json` reports:

```text
reference_reproduced = true
rejected_non_reference_policies = 3
guard_validated = true
```

## Decision

Close M141 as a positive harness result.

The guard is cheap enough to run before strict miners and catches the exact
failure M139 missed. It should become a pre-screen for future repair candidates:
do not run a full strict proof-surface miner or PPO continuation on a candidate
that fails the protected-key replay guard.

## Next Step

M142 should use the M141 guard as a pre-screen for a minimal repair path. A
candidate should only proceed if it:

```text
1. passes the critical-key guard;
2. preserves behavior and zero-response degradation;
3. does not materially regress fixed M136/M128 losses;
4. keeps the actor input contract unchanged.
```
