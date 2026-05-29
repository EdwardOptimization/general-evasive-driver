# M1456 Paper-Route Source-Step Boundary Retarget Implementation

## Summary

M1456 implements the source-step replay boundary retarget proposal generator
admitted by M1455.

Decision:

```text
source_step_boundary_retarget_generator_implemented_admit_proposal_smoke
```

M1456 does not run preflight, bounded replay, training, PPO, promotion, private
holdout, corpus export, or actor-input changes.

## Implementation

Added:

```text
src/autodrift/source_step_replay_boundary_retarget.py
tests/test_source_step_replay_boundary_retarget.py
```

The generator consumes M1452 actual replay rows and emits source-step retarget
proposal rows. It classifies each history-variant source group as:

```text
normal_boundary
too_easy
too_hard
```

and generates conservative relocation proposal deltas:

```text
too_easy: increase pressure
too_hard: relax pressure
normal_boundary: local perturbation around the current relocation
```

All emitted candidates preserve:

```text
candidate_step_column: source_step
source_step
candidate_step
reveal_step
```

## Tests

Focused command:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_source_step_replay_boundary_retarget.py
```

Result:

```text
4 passed in 0.91s
```

Covered behavior:

```text
boundary-pressure classification
class-specific retarget delta direction
source_step preservation
control variants excluded from proposal bases
selection caps and normal_boundary priority
```

## Guardrails

M1456 guardrail status:

```text
source_preflight_started: false
replay_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next Route

Admit:

```text
m1457-paper-route-source-step-boundary-retarget-smoke
```

M1457 should run the proposal generator on M1452 actual replay rows and write a
retarget candidate pool only. It must not run preflight, bounded replay,
training, PPO, promotion, private holdout, corpus export, or actor-input
changes.
