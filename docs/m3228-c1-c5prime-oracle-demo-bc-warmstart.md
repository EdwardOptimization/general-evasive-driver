# M3228: C1 C5-prime Oracle Demo + BC Warm-start

Status: failed. This was the first C1 warm-start attempt after CP-1
conditional approval. It is engineering-only behavior pretraining evidence and
does not admit C2, mutate the incumbent, or make a driver-performance,
validation, promotion, high-fidelity, paper, repair-success,
robustness-result, feasibility-proof, or self-ID claim.

## Artifacts

- Manifest: `experiments/manifests/m3228-c1-c5prime-oracle-demo-bc-warmstart.json`
- Preregistration: `experiments/feasibility_audit/c5prime_c1_oracle_bc_prereg.json`
- Quick smoke: `experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart_quick.json`
- Full summary: `experiments/feasibility_audit/c5prime_c1_oracle_bc_warmstart.json`
- Full checkpoint: `runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full/checkpoint.pt`
- Full dataset: `runs/feasibility_audit/c5prime_c1_oracle_bc_warmstart/full/dataset.npz`
- Harness log: `runs/research/m3228-c1-c5prime-oracle-demo-bc-warmstart_20260612T040431Z/command.log`

## Preregistered Gate

M3228 selected one reproducible structured-oracle A3 row per
S1/S2/S3 T-limit instance, split by frozen row hash into train, selection,
and validation roles. The BC model was a 72-observation MLP actor head using
held-out selection loss for epoch selection plus a DAgger-lite relabeling pass
on train-role rows.

The frozen smoke gate required:

- all structured-oracle demos replay to success;
- checkpoint and dataset artifacts are written;
- validation action MSE <= 0.12;
- validation action MSE at least 25% lower than the zero-action baseline.

## Measured Result

Quick smoke passed on six rows:

- validation action MSE: `0.071962`;
- zero-action baseline MSE: `0.512365`;
- demo replay, checkpoint, and dataset gates: pass.

Full run failed:

| readout | value |
|---|---:|
| selected rows | 36 |
| role counts | train 17 / selection 9 / validation 10 |
| demo replay gate | pass |
| checkpoint + dataset gates | pass |
| validation action MSE | 0.234184 |
| zero-action baseline MSE | 0.501099 |
| validation BC rollout success context | 5/10 |
| preregistered MSE gate | fail |

The command returned `1` only after writing the full summary/checkpoint/dataset
artifacts, because the validation action-MSE gate failed.

## Decision

M3228 is a failed C1 warm-start attempt. C1 remains open. Do not use the quick
smoke or the 5/10 validation rollout context to admit C2.

The immediate follow-up is M3229 failure localization, using the failed
checkpoint and frozen labels without retraining or changing the M3228 gate.
