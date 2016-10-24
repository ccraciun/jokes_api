.PHONY: env test clean purge repl run

VENV_PYTHON ?= python
VENV_NAME ?= env

repl: $(VENV_NAME)
	. $(VENV_NAME)/bin/activate; ipython

run: $(VENV_NAME)
	. $(VENV_NAME)/bin/activate; pip install -e .; jokes

test: $(VENV_NAME)
	. $(VENV_NAME)/bin/activate; python setup.py test

clean:
	$(VENV_PYTHON) setup.py clean
	find . -type f -name "*.pyc" -exec rm {} \;

purge: clean
	rm -rf $(VENV_NAME) dist build *.egg-info

$(VENV_NAME): $(VENV_NAME)/bin/activate

$(VENV_NAME)/bin/activate: setup.py requirements.txt
	test -d $(VENV_NAME) || virtualenv -p $(VENV_PYTHON) --no-site-packages $(VENV_NAME)
	. $(VENV_NAME)/bin/activate ; pip install -U pip wheel
	. $(VENV_NAME)/bin/activate ; pip install -r requirements.txt
	touch $(VENV_NAME)/bin/activate
