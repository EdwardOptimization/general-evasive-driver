PYTHON ?= python
PYTHONPATH ?= src
CONDA_ENV ?= autodrift

.PHONY: env-create env-update test eval-heuristic train-smoke clean

env-create:
	mamba env create -f environment.yml -y
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

env-update:
	mamba env update -n $(CONDA_ENV) -f environment.yml --prune
	conda run -n $(CONDA_ENV) python -m pip install --no-deps -e .

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

eval-heuristic:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.evaluate --episodes 5 --policy heuristic

train-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m autodrift.train_ppo --total-steps 512 --rollout-steps 128 --eval-episodes 1

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache .mypy_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
