.PHONY: build build-compose build-artifact dev clean clean-docker clean-js

build: build-compose build-artifact

build-compose:
	docker-compose build --no-cache

build-compose-with-cache:
	docker-compose build

build-artifact:
	docker build --no-cache -t loktar/storage_proxy .

build-with-cache:
	docker build -t loktar/storage_proxy .

local:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --service-ports storage_proxy dev local

prod:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --service-ports storage_proxy prod

shell:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --service-ports storage_proxy shell

clean: clean-build clean-pyc clean-docker clean-test

clean-docker:
	docker-compose kill
	docker-compose rm --all -fv

clean-build:
	rm -rf ./src/build/
	rm -rf ./src/dist/
	rm -rf ./src/*egg*/

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*.~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -rf {} +

clean-test:
	rm -f ./app/.coverage
	rm -fr ./app/htmlcov/
	rm -rf ./app/.cache
	rm -rf ./app/coverage.xml

lint:
	docker-compose run --no-deps storage_proxy flake8 storage_proxy

test:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml run --service-ports storage_proxy test
