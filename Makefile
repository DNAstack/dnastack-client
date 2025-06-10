PY_VERSION_BASELINE=3.8
PY_VERSION_STABLE=3.11
PY_VERSION_LATEST=3.12
TESTING_IMAGE_NAME=dnastack/client-library-testing

.PHONY: run-notebooks
run-notebooks:
	docker run -it --rm \
		-v $$(pwd)/samples:/workspace \
		--workdir /workspace \
		-p 8888:8888 \
		jupyter/scipy-notebook

.PHONY: run-notebooks-dev
run-notebooks-dev:
	docker run -it --rm \
		-v $$(pwd)/samples:/workspace \
		-v $$(pwd)/:/opt/src \
		--workdir /workspace \
		-p 8888:8888 \
		jupyter/scipy-notebook

.PHONY: reset
reset:
	rm -rf ~/.dnastack/config.yaml
	rm -rf ~/.dnastack/sessions/*

.PHONY: test-all
test-all:
	E2E_ENV_FILE=.env ./scripts/run-e2e-tests.sh

.PHONY: package-test
package-test:
	mkdir -p dist; rm dist/*; ./scripts/build-package.py --pre-release a
	docker run -it --rm \
		-v $$(pwd)/dist:/dist-test \
		--workdir /dist-test \
		python:$(PY_VERSION_BASELINE)-slim \
		bash -c "pip install *.whl && dnastack use --no-auth viral.ai"

.PHONY: docker-test-all
docker-test-all: docker-test-all-python-oldest-stable docker-test-all-python-latest-stable docker-test-all-python-rc

# Terminal for testing
.PHONY: docker-test-all-baseline
docker-test-all-baseline:
	make TESTING_PYTHON=python:$(PY_VERSION_BASELINE)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the oldest stable version.
.PHONY: docker-test-all-baseline
docker-test-all-baseline:
	make TESTING_PYTHON=python:$(PY_VERSION_BASELINE)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the latest stable version.
.PHONY: docker-test-all-stable
docker-test-all-stable:
	make TESTING_PYTHON=python:$(PY_VERSION_STABLE)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the release candidate version.
.PHONY: docker-test-all-latest
docker-test-all-latest:
	make TESTING_PYTHON=python:$(PY_VERSION_LATEST)-slim WEBDRIVER_DISABLED=false docker-test-all-solo

# Testing the anaconda release.
.PHONY: docker-test-all-anaconda
docker-test-all-anaconda:
	make TESTING_PYTHON=continuumio/miniconda3 WEBDRIVER_DISABLED=false docker-test-all-solo

.PHONY: docker-test-all-pypy
docker-test-all-pypy:
	make TESTING_PYTHON=pypy WEBDRIVER_DISABLED=false docker-test-all-solo

.PHONY: docker-test-all-solo
docker-test-all-solo:
	./scripts/build-e2e-test-image.sh $(TESTING_PYTHON)
	./scripts/run-e2e-tests-locally-in-docker.sh $(TESTING_PYTHON)
