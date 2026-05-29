# M1408 Paper-Route Staged Obstacle Warmup API Implementation

## Summary

M1408 implements the disabled-by-default staged warmup gate API selected by
M1407.

Decision:

```text
staged_obstacle_warmup_api_implemented_route_to_branch_synthesis_before_source_smoke
```

M1408 does not run source smoke, outcome interventions, training, PPO, promote,
use private holdout, export a training corpus, or change the actor input
contract.

## Implementation

Code changes:

```text
src/autodrift/env.py
  - added WarmupGateConfig
  - added disabled-by-default DriftEnvConfig.warmup_gate
  - added staged slot0 warmup gate diagnostics
  - slot0 shows warmup gate while active/visible
  - slot0 switches back to emergency obstacle after pass or timeout
  - default obstacle behavior remains unchanged when warmup_gate.enabled=false

src/autodrift/config.py
  - build_env_config and merge_env_config now support warmup_gate

tests/test_env.py
  - default disabled behavior test
  - warmup gate visible before emergency reveal test
  - warmup gate to emergency obstacle switch test
  - warmup gate JSON config loading test
```

The implementation uses existing obstacle geometry semantics. It does not add a
new actor observation channel.

## Contract

Default mainline actor shape remains:

```text
base_obs_dim: 72
observation shape: (72,)
```

Warmup gate is explicit opt-in:

```text
warmup_gate.enabled: false by default
```

When enabled:

```text
active_obstacle_kind: warmup_gate | emergency_obstacle | none
warmup_gate_active: bool
warmup_gate_visible: bool
warmup_gate_passed: bool
warmup_gate_collision: bool
warmup_gate_min_clearance: float
warmup_gate_clearance_margin: float
```

These info fields are diagnostics/logging. They are not actor inputs.

## Verification

Focused tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q tests/test_config.py tests/test_env.py
```

Result:

```text
44 passed
```

Full tests:

```bash
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=src python -m pytest -q
```

Result:

```text
1387 passed, 4 warnings
```

Compile check:

```bash
python -m compileall -q src tests
```

Result:

```text
passed
```

## Not Claimed

M1408 is infrastructure only:

```text
source_smoke_started: false
outcome_probe_started: false
training_started: false
ppo_used: false
promoted: false
private_holdout_used: false
training_corpus_exported: false
actor_input_contract_changed: false
level3_self_id_claim_made: false
```

## Next

The workflow cadence requires M1409 to synthesize the M1399-M1408 branch before
source smoke. If synthesis continues the branch, the next source-smoke step
should:

```text
1. extend source smoke reporting with warmup gate diagnostics;
2. create staged warmup gate configs;
3. run no-training source smoke;
4. report source diversity, matched/bucketed current rows, and warmup command-
   response evidence diagnostics.
```

M1409 must not run outcome interventions, train, run PPO, promote, use private
holdout, export a training corpus, or claim self-identification from source
materialization.
