SHELL := /bin/bash

VENV = venv

.PHONY: dev
dev: $(VENV)/pyvenv.cfg

.PHONY: run
run: $(VENV)/pyvenv.cfg  ## run bot with test configuration
	@. $(VENV)/bin/activate && PYTHONPATH=src/ python -u src/solbot/main.py

.PHONY: test
test: $(VENV)/pyvenv.cfg  ## run test bot with test configuration
	@. $(VENV)/bin/activate && PYTHONPATH=src/ python -u src/solbot/web3/jito.py

$(VENV)/pyvenv.cfg: requirements.txt  ## create python 3 virtual environment
	python3.10 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements.txt
	$(VENV)/bin/python -m pip install --editable .
	$(VENV)/bin/python tasks.py fix-venv

.PHONY: dist
dist:
	$(VENV)/bin/python -m pip install build
	$(VENV)/bin/python -m build --sdist

.PHONY: solbot
solbot:  ## run solbot in background
	PYTHONPATH=src/ nohup venv/bin/python -u src/solbot/main.py >> solbot.log 2>&1 &

kill:  ## kill running bot
	pkill -U $$USER -f "src/solbot/main.py"
	pkill -U $$USER -f "make run"
