PYTHON ?= python
PYTHONPATH ?= src
PYTEST_THREAD_ENV ?= OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
CONDA_ENV ?= autodrift
M7_ENV_CONFIG ?= configs/m7_obstacle_aes_weighted_holdout_eval.json
M7_CORPUS_RUN_DIR ?= runs/scenario_corpus_m7_aes_weighted_seed1300
M7_SEED_CSV ?= $(M7_CORPUS_RUN_DIR)/scenario_corpus.csv
M7_GATE_RUN_DIR ?= runs/m7_gate_aes_weighted_corpus_seed1300
M7_PER_LABEL ?= 20
M7_MAX_CANDIDATES ?= 1000
M7_EPISODES ?= 100
M7_PROBE_EPISODES ?= 100
M7_PROBE_EPOCHS ?= 160
M7_DEVICE ?= cpu
M8_DRIVER_NAME ?= m8
M8_CHECKPOINT ?=
M8_GATE_RUN_DIR ?= runs/m8_driver_gate_seed227
RESEARCH_QUEUE ?= experiments/research_queue.csv
RESEARCH_STATUS ?= experiments/research_status.json
RESEARCH_LOG ?= docs/research-log.md
RESEARCH_MANIFEST_DIR ?= experiments/manifests
RESEARCH_SCOREBOARD ?= experiments/scoreboard.csv

.PHONY: env-create env-create-cpu env-update env-update-cpu torch-gpu torch-cpu test test-light check-diff hooks-install eval-heuristic train-smoke benchmark-smoke rollout-smoke m7-corpus m7-gate-smoke m7-gate m8-driver-gate-smoke m8-driver-gate research-plan research-run-next research-validate clean

env-create:
	mamba env create -f environment-gpu.yml -y
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

env-create-cpu:
	mamba env create -f environment.yml -y
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

env-update:
	mamba env update -n $(CONDA_ENV) -f environment-gpu.yml --prune
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

env-update-cpu:
	mamba env update -n $(CONDA_ENV) -f environment.yml --prune
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

torch-gpu:
	conda run -n $(CONDA_ENV) python -m pip install --force-reinstall --index-url https://download.pytorch.org/whl/cu130 torch==2.12.0+cu130

torch-cpu:
	conda run -n $(CONDA_ENV) python -m pip install --force-reinstall --index-url https://download.pytorch.org/whl/cpu torch==2.12.0+cpu

test:
	$(PYTEST_THREAD_ENV) PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

test-light:
	$(PYTEST_THREAD_ENV) PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q tests/test_m7_gate.py tests/test_scenario_corpus.py tests/test_benchmark.py tests/test_research_cycle.py

check-diff:
	git diff --check
	git diff --cached --check

hooks-install:
	install -m 0755 scripts/hooks/pre-commit .git/hooks/pre-commit

eval-heuristic:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.evaluate --episodes 5 --policy heuristic

train-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.train_ppo --config configs/ppo_smoke.json

benchmark-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.benchmark --episodes 2 --policies heuristic random

rollout-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.rollout --policy heuristic --seeds 7 --out-dir /tmp/autodrift_rollout_smoke

m7-corpus:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.scenario_corpus \
		--env-config $(M7_ENV_CONFIG) \
		--seed-start 1300 \
		--per-label $(M7_PER_LABEL) \
		--max-candidates $(M7_MAX_CANDIDATES) \
		--run-dir $(M7_CORPUS_RUN_DIR)

m7-gate-smoke: m7-corpus
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.m7_gate \
		--env-config $(M7_ENV_CONFIG) \
		--seed-csv $(M7_SEED_CSV) \
		--episodes 6 \
		--seed 900 \
		--probe-episodes 6 \
		--probe-seed 1200 \
		--probe-epochs 20 \
		--device $(M7_DEVICE) \
		--run-dir runs/m7_gate_smoke \
		--skip-probes

m7-gate: m7-corpus
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.m7_gate \
		--env-config $(M7_ENV_CONFIG) \
		--seed-csv $(M7_SEED_CSV) \
		--episodes $(M7_EPISODES) \
		--seed 900 \
		--probe-episodes $(M7_PROBE_EPISODES) \
		--probe-seed 1200 \
		--probe-epochs $(M7_PROBE_EPOCHS) \
		--device $(M7_DEVICE) \
		--run-dir $(M7_GATE_RUN_DIR)

m8-driver-gate-smoke: m7-corpus
	test -n "$(M8_CHECKPOINT)" || { echo "Set M8_CHECKPOINT to a same-contract clean driver checkpoint"; exit 2; }
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.m7_gate \
		--env-config $(M7_ENV_CONFIG) \
		--seed-csv $(M7_SEED_CSV) \
		--episodes $(M7_EPISODES) \
		--seed 900 \
		--probe-episodes 6 \
		--probe-seed 1200 \
		--probe-epochs 20 \
		--device $(M7_DEVICE) \
		--run-dir $(M8_GATE_RUN_DIR) \
		--skip-probes \
		--driver-checkpoint $(M8_CHECKPOINT) \
		--driver-name $(M8_DRIVER_NAME)

m8-driver-gate: m7-corpus
	test -n "$(M8_CHECKPOINT)" || { echo "Set M8_CHECKPOINT to a same-contract clean driver checkpoint"; exit 2; }
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.m7_gate \
		--env-config $(M7_ENV_CONFIG) \
		--seed-csv $(M7_SEED_CSV) \
		--episodes $(M7_EPISODES) \
		--seed 900 \
		--probe-episodes $(M7_PROBE_EPISODES) \
		--probe-seed 1200 \
		--probe-epochs $(M7_PROBE_EPOCHS) \
		--device $(M7_DEVICE) \
		--run-dir $(M8_GATE_RUN_DIR) \
		--driver-checkpoint $(M8_CHECKPOINT) \
		--driver-name $(M8_DRIVER_NAME)

research-plan:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.research_cycle \
		--mode plan \
		--queue $(RESEARCH_QUEUE) \
		--status $(RESEARCH_STATUS) \
		--log $(RESEARCH_LOG)

research-run-next:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.research_cycle \
		--mode run-next \
		--queue $(RESEARCH_QUEUE) \
		--status $(RESEARCH_STATUS) \
		--log $(RESEARCH_LOG)

research-validate:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.research_validate \
		--queue $(RESEARCH_QUEUE) \
		--status $(RESEARCH_STATUS) \
		--manifest-dir $(RESEARCH_MANIFEST_DIR) \
		--scoreboard $(RESEARCH_SCOREBOARD)

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
