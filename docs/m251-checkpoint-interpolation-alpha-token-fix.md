# M251 Checkpoint Interpolation Alpha Token Fix

M251 fixes an infrastructure issue found during M250. The built-in
checkpoint interpolation sweep rounded file tokens to three decimals and labels
to thousandths, so sub-`0.001` alphas collided. That made the discarded M250
artifact invalid for micro/nano decisions:

```text
runs/m250_micro_m239_to_protected_source_interpolation
```

No PPO was run and checkpoint tensor interpolation semantics are unchanged.

## Change

`src/autodrift/checkpoint_interpolation.py` now:

- keeps file tokens at up to nine decimal places;
- preserves legacy labels for common thousandth-aligned alphas such as
  `0.125 -> a125` and `0.5 -> a500`;
- uses decimal labels for non-thousandth micro/nano alphas such as
  `0.00025 -> a0_00025`.

## Precision Smoke

Run directory:

```text
runs/m251_alpha_token_precision_smoke
```

The fixed sweep writes distinct labels and paths:

| Alpha | Policy label | File |
| ---: | --- | --- |
| 0.0001 | m251_a0_0001 | alpha_0_0001.pt |
| 0.00025 | m251_a0_00025 | alpha_0_00025.pt |
| 0.0005 | m251_a0_0005 | alpha_0_0005.pt |
| 0.0025 | m251_a0_0025 | alpha_0_0025.pt |
| 0.125 | m251_a125 | alpha_0_125.pt |
| 0.5 | m251_a500 | alpha_0_5.pt |

## Verification

Focused tests:

```text
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_checkpoint_interpolation.py
```

Result:

```text
6 passed
```

Research validation:

```text
make research-validate
```

Result:

```text
research validation passed
```

## Decision

M251 is an infrastructure completion, not a driver promotion.

Next step:

```text
m252-nano-alpha-safety-boundary-audit
```
