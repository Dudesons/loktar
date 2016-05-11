.PHONY: clean-pyc clean-build docs clean

help:
	@echo "all - check style with flake8, check code coverage and run the tests, generate the Sphinx documentation, and runs the server."
	@echo "all-deps - Does the same as all but installs the test and regular dependencies beforehand"
	@echo "ci - Command used by the CI"
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

all: lint coverage docs

all-deps: deps test-deps lint coverage docs

ci: lint test

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

deps:
	pip install -r requirements.txt --upgrade

test-deps:
	pip install -r test_requirements.txt --upgrade
	pip install flake8 hacking --upgrade
	pip install pytest-cov --upgrade
	pip install sphinx --upgrade

lint:
	flake8 loktar tests

test:
	PYTHONPATH=$(shell pwd) py.test tests/

coverage:
	PYTHONPATH=$(shell pwd) py.test -s --cov=loktar --cov-report html --cov-report xml --cov-config .coveragerc tests/

docs:
	rm -f docs/traxit_ci.rst
	rm -f docs/modules.rst
	sphinx-apidoc -o docs/ traxit_ci -e
	$(MAKE) -C docs clean
	$(MAKE) -C docs html

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	python setup.py install
