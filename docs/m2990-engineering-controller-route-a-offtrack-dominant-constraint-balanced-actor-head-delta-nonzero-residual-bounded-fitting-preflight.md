# M2990 Engineering Controller Route A Actor-Head Delta Nonzero Residual Bounded Fitting Preflight

## Summary

- status pass: `True`
- gate matrix pass: `True`
- required artifacts present: `True`
- fitting dataset rows: `43`
- fitting samples: `4204`
- initial weighted MSE: `0.0010713406183980136`
- final weighted MSE: `0.000613389726277548`
- success guard rows: `13`
- success guard predicted residual abs max: `0.07999999821186066`
- stale exclusion rows: `11`
- target quality validated: `False`
- bounded offline fitting run: `True`
- validation run: `False`
- ranking run: `False`
- checkpoint mutated: `False`
- next blocker: `m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-result-audit`
- follow-up manifest: `experiments/manifests/m2991-engineering-controller-route-a-offtrack-dominant-constraint-balanced-actor-head-delta-nonzero-residual-bounded-fitting-result-audit.json`

## Boundary

M2990 performs bounded offline fitting only. It writes a candidate linear
residual-head artifact and loss trace for M2991 audit, while preserving actor
observation/action `72/action 3`,
keeping target labels and provenance actor-invisible, keeping success rows as
zero-target guard checks, and keeping stale guardrails excluded.

M2990 does not run an environment, validate a policy, rank candidates, select a
winner, mutate or promote checkpoints, or claim repair success, driver
performance, paper evidence, current-sim verdict, high-fidelity validation,
finite-window-vs-GRU evidence, full-driver completion, or self-ID evidence.
