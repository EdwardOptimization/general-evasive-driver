# M2993 Engineering Controller Route A Actor-Head Delta Nonzero Residual Success-Identity Guard-Constrained Fitting Preflight

## Summary

- status pass: `True`
- gate matrix pass: `True`
- required artifacts present: `True`
- fitting dataset rows: `43`
- fitting samples: `4204`
- initial candidate weighted MSE: `0.0010713406183980136`
- final candidate weighted MSE: `0.001065189191153038`
- M2990 success guard predicted residual abs max: `0.07999999821186066`
- M2993 success guard predicted residual abs max: `0.00034158502239733934`
- success guard required abs max: `0.001`
- success guard improved from M2990: `True`
- success guard zero residual satisfied: `True`
- stale exclusion rows: `11`
- target quality validated: `False`
- guard-constrained offline fitting run: `True`
- validation run: `False`
- ranking run: `False`
- checkpoint mutated: `False`
- next blocker: `m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit`
- follow-up manifest: `experiments/manifests/m2994-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-success-identity-guard-constrained-fitting-result-audit.json`

## Boundary

M2993 performs guard-constrained offline fitting only. It writes a candidate
linear residual-head artifact and constrained loss trace for M2994 audit while
preserving actor observation/action `72/3`.
Candidate rows remain the fitting denominator; success identity rows are
zero-residual guard penalty or constraint rows; stale fixed-source guardrails
remain excluded.

M2993 does not run an environment, validate a policy, rank candidates, select a
winner, mutate or promote checkpoints, or claim target quality, repair success,
driver performance, paper evidence, current-sim verdict, high-fidelity
validation, finite-window-vs-GRU evidence, full-driver completion, or self-ID
evidence.
